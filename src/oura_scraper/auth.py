"""OAuth2 authentication for Oura API.

Handles the OAuth2 authorization flow, token exchange, and refresh.
Refresh tokens are single-use - they are invalidated after each use
and a new refresh token is returned.
"""

import json
import logging
import secrets
import urllib.parse
import webbrowser
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, Protocol

import httpx

from oura_scraper.config import get_default_token_path, get_settings

logger = logging.getLogger(__name__)


class TokenStorageProtocol(Protocol):
    """Protocol for token storage backends."""

    def save(self, tokens: "OAuthTokens") -> None:
        """Save tokens to storage."""
        ...

    def load(self) -> "OAuthTokens | None":
        """Load tokens from storage."""
        ...

    def clear(self) -> None:
        """Clear stored tokens."""
        ...

AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"

ALL_SCOPES = ["email", "personal", "daily", "heartrate", "workout", "tag", "session", "spo2"]


@dataclass
class OAuthTokens:
    """OAuth2 token data."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "bearer"

    def is_expired(self) -> bool:
        """Check if access token is expired (with 5 min buffer)."""
        return datetime.now(UTC) >= (self.expires_at - timedelta(minutes=5))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OAuthTokens":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            token_type=data.get("token_type", "bearer"),
        )

    @classmethod
    def from_token_response(cls, response: dict[str, Any]) -> "OAuthTokens":
        """Create from Oura API token response."""
        expires_in = response.get("expires_in", 86400)  # Default 24h
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        return cls(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            expires_at=expires_at,
            token_type=response.get("token_type", "bearer"),
        )


class TokenStorage:
    """File-based token storage.

    Stores tokens in a JSON file. For production, consider using
    a secrets manager like Azure Key Vault.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize token storage.

        Args:
            path: Path to token file. Defaults to ~/.config/oura-scraper/tokens.json.
        """
        if path is None:
            settings = get_settings()
            # Use setting if provided, otherwise use default config path
            token_path = settings.token_path if settings.token_path else get_default_token_path()
            self.path = Path(token_path)
        else:
            self.path = path

    def save(self, tokens: OAuthTokens) -> None:
        """Save tokens to file."""
        # Create parent directory if it doesn't exist
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(tokens.to_dict(), indent=2))
        self.path.chmod(0o600)  # Restrict permissions
        logger.info("Tokens saved to %s", self.path)

    def load(self) -> OAuthTokens | None:
        """Load tokens from env vars or file.

        Priority: env vars > file
        """
        # First try env vars (for containerized deployments)
        settings = get_settings()
        if settings.access_token and settings.refresh_token:
            logger.debug("Loading tokens from environment variables")
            return OAuthTokens(
                access_token=settings.access_token,
                refresh_token=settings.refresh_token,
                expires_at=datetime.now(UTC) + timedelta(days=365),  # Assume valid
                token_type="bearer",
            )

        # Fall back to file
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text())
            return OAuthTokens.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load tokens: %s", e)
            return None

    def clear(self) -> None:
        """Delete stored tokens."""
        if self.path.exists():
            self.path.unlink()
            logger.info("Tokens cleared")


class DatabaseTokenStorage:
    """Database-backed token storage for stateless container deployments.

    Stores tokens in PostgreSQL, ensuring they persist across container restarts
    and token refreshes. This follows 12-factor app principles by treating the
    database as a backing service for state persistence.
    """

    def __init__(self, database_url: str) -> None:
        """Initialize database token storage.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url

    def save(self, tokens: OAuthTokens) -> None:
        """Save tokens to database using upsert."""
        import psycopg

        with psycopg.connect(self.database_url) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO oauth_tokens
                    (id, access_token, refresh_token, expires_at, token_type, updated_at)
                VALUES (1, %(access_token)s, %(refresh_token)s, %(expires_at)s,
                        %(token_type)s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    token_type = EXCLUDED.token_type,
                    updated_at = NOW()
                """,
                {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                    "expires_at": tokens.expires_at,
                    "token_type": tokens.token_type,
                },
            )
            conn.commit()
        logger.info("Tokens saved to database")

    def load(self) -> OAuthTokens | None:
        """Load tokens from env vars or database.

        Priority: env vars > database
        """
        import psycopg

        # First try env vars (for initial bootstrap)
        settings = get_settings()
        if settings.access_token and settings.refresh_token:
            logger.debug("Loading tokens from environment variables")
            return OAuthTokens(
                access_token=settings.access_token,
                refresh_token=settings.refresh_token,
                expires_at=datetime.now(UTC) + timedelta(days=365),
                token_type="bearer",
            )

        # Fall back to database
        try:
            with psycopg.connect(self.database_url) as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT access_token, refresh_token, expires_at, token_type
                    FROM oauth_tokens
                    WHERE id = 1
                    """
                )
                row = cur.fetchone()
                if row:
                    logger.debug("Loading tokens from database")
                    return OAuthTokens(
                        access_token=row[0],
                        refresh_token=row[1],
                        expires_at=row[2],
                        token_type=row[3] or "bearer",
                    )
        except psycopg.Error as e:
            logger.warning("Failed to load tokens from database: %s", e)

        return None

    def clear(self) -> None:
        """Delete stored tokens from database."""
        import psycopg

        with psycopg.connect(self.database_url) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM oauth_tokens WHERE id = 1")
            conn.commit()
        logger.info("Tokens cleared from database")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""

    authorization_code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            OAuthCallbackHandler.error = params["error"][0]
            self._send_response("Authorization denied. You can close this window.")
        elif "code" in params:
            OAuthCallbackHandler.authorization_code = params["code"][0]
            OAuthCallbackHandler.state = params.get("state", [None])[0]
            self._send_response("Authorization successful! You can close this window.")
        else:
            self._send_response("Invalid callback. Missing code parameter.", status=400)

    def _send_response(self, message: str, status: int = 200) -> None:
        """Send HTTP response."""
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"<html><body><h1>{message}</h1></body></html>"
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass


class OuraAuth:
    """Oura OAuth2 authentication handler."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_storage: TokenStorageProtocol | None = None,
    ) -> None:
        """Initialize OAuth handler.

        Args:
            client_id: Oura OAuth client ID. Defaults to OURA_CLIENT_ID env var.
            client_secret: Oura OAuth client secret. Defaults to OURA_CLIENT_SECRET env var.
            token_storage: Token storage backend. Defaults to file storage.
        """
        settings = get_settings()
        self.client_id = client_id or settings.client_id
        self.client_secret = client_secret or settings.client_secret
        self.storage: TokenStorageProtocol = token_storage or TokenStorage()
        self._tokens: OAuthTokens | None = None

    def get_authorization_url(
        self,
        redirect_uri: str = "http://localhost:8080/callback",
        scopes: list[str] | None = None,
    ) -> tuple[str, str]:
        """Generate authorization URL.

        Args:
            redirect_uri: Callback URL for authorization
            scopes: List of scopes to request. Defaults to all scopes.

        Returns:
            Tuple of (authorization_url, state)
        """
        state = secrets.token_urlsafe(32)
        scope_str = " ".join(scopes or ALL_SCOPES)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_str,
            "state": state,
        }

        url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        return url, state

    def exchange_code(
        self,
        code: str,
        redirect_uri: str = "http://localhost:8080/callback",
    ) -> OAuthTokens:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Must match the redirect_uri used in authorization

        Returns:
            OAuth tokens
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = httpx.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        tokens = OAuthTokens.from_token_response(response.json())
        self.storage.save(tokens)
        self._tokens = tokens
        logger.info("Authorization successful, tokens stored")
        return tokens

    def refresh_tokens(self, refresh_token: str | None = None) -> OAuthTokens:
        """Refresh access token using refresh token.

        Note: Refresh tokens are single-use! The old refresh token is
        invalidated and a new one is returned.

        Args:
            refresh_token: Refresh token. If not provided, uses stored token.

        Returns:
            New OAuth tokens (both access and refresh tokens are new)
        """
        if refresh_token is None:
            tokens = self.storage.load()
            if tokens is None:
                raise ValueError("No stored tokens and no refresh_token provided")
            refresh_token = tokens.refresh_token

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = httpx.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        tokens = OAuthTokens.from_token_response(response.json())
        self.storage.save(tokens)
        self._tokens = tokens
        logger.info("Tokens refreshed successfully")
        return tokens

    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token
        """
        # Try cached tokens first
        if self._tokens and not self._tokens.is_expired():
            return self._tokens.access_token

        # Try loading from storage
        tokens = self.storage.load()
        if tokens is None:
            raise ValueError("No tokens available. Run 'oura-scraper auth' first.")

        # Refresh if expired
        if tokens.is_expired():
            logger.info("Access token expired, refreshing...")
            tokens = self.refresh_tokens(tokens.refresh_token)

        self._tokens = tokens
        return tokens.access_token

    def authorize_interactive(
        self,
        port: int = 8080,
        open_browser: bool = True,
    ) -> OAuthTokens:
        """Run interactive authorization flow.

        Starts a local HTTP server to capture the OAuth callback,
        opens the browser for user authorization, and exchanges
        the code for tokens.

        Args:
            port: Local port for callback server
            open_browser: Whether to automatically open browser

        Returns:
            OAuth tokens
        """
        redirect_uri = f"http://localhost:{port}/callback"
        auth_url, expected_state = self.get_authorization_url(redirect_uri)

        # Reset handler state
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.state = None
        OAuthCallbackHandler.error = None

        # Start callback server
        server = HTTPServer(("localhost", port), OAuthCallbackHandler)
        server_thread = Thread(target=server.handle_request)
        server_thread.start()

        logger.info("Opening browser for authorization...")
        logger.info("If browser doesn't open, visit: %s", auth_url)

        if open_browser:
            webbrowser.open(auth_url)

        # Wait for callback
        server_thread.join(timeout=300)  # 5 minute timeout
        server.server_close()

        if OAuthCallbackHandler.error:
            raise ValueError(f"Authorization failed: {OAuthCallbackHandler.error}")

        if OAuthCallbackHandler.authorization_code is None:
            raise ValueError("Authorization timed out or failed")

        if OAuthCallbackHandler.state != expected_state:
            raise ValueError("State mismatch - possible CSRF attack")

        # Exchange code for tokens
        return self.exchange_code(OAuthCallbackHandler.authorization_code, redirect_uri)
