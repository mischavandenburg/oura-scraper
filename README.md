# Oura Scraper

A Python CLI tool that scrapes health metrics from the Oura Ring API and stores them in PostgreSQL. Designed to run as a containerized CronJob on Kubernetes.

## Features

- OAuth2 authentication with automatic token refresh
- **Database token storage** for stateless container deployments (12-factor compliant)
- **Encrypted tokens at rest** using Fernet symmetric encryption
- Scrapes all 17 Oura API v2 endpoints
- Upserts data to PostgreSQL (safe to re-run)
- Configurable scrape window (default: 7 days)
- Multi-stage Docker image (~50MB)
- Kubernetes-ready with environment variable configuration

## Getting OAuth Tokens

Before using the scraper, you need to obtain OAuth tokens from Oura.

### 1. Create an Oura Application

1. Go to [Oura Developer Portal](https://cloud.ouraring.com/oauth/applications)
2. Create a new application
3. Set the callback URL to `http://localhost:8080/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Run the Auth Flow

```bash
# Set your OAuth credentials
export OURA_CLIENT_ID=your_client_id
export OURA_CLIENT_SECRET=your_client_secret

# Start the OAuth flow
uv run oura-scraper auth
```

This will:
1. Open your browser to the Oura authorization page
2. Start a local server on `http://localhost:8080`
3. After you authorize, Oura redirects back with the tokens
4. Tokens are saved to `~/.config/oura-scraper/tokens.json`

### 3. Use the Tokens

For local development, the scraper reads from the token file automatically.

For containerized deployments, set the tokens as environment variables for initial bootstrap:

```bash
export OURA_ACCESS_TOKEN=<access_token from json>
export OURA_REFRESH_TOKEN=<refresh_token from json>
```

### Important: Token Refresh Behavior

Oura refresh tokens are **single-use**. Each time the access token expires and is refreshed, a new refresh token is issued and the old one is invalidated.

For containerized deployments, the scraper uses **database token storage**:

1. On first run, tokens are loaded from environment variables (bootstrap)
2. After the first token refresh, new tokens are saved to the database
3. Subsequent runs load tokens from the database (not env vars)
4. This ensures tokens persist across container restarts

The token loading priority is: **Database → Environment Variables**

## Quick Start

### Local Development

```bash
# Install dependencies
uv sync

# Set up environment
export OURA_DB_HOST=localhost
export OURA_DB_PASSWORD=yourpassword
export OURA_ACCESS_TOKEN=your_token
export OURA_REFRESH_TOKEN=your_refresh_token

# Initialize database schema
uv run oura-scraper init-db

# Run scraper
uv run oura-scraper scrape
```

### Docker

```bash
docker run --rm \
  -e OURA_DB_HOST=db.example.com \
  -e OURA_DB_PASSWORD=secret \
  -e OURA_ACCESS_TOKEN=token \
  -e OURA_REFRESH_TOKEN=refresh \
  ghcr.io/mischavandenburg/oura-scraper:latest scrape
```

## CLI Commands

```bash
oura-scraper --help              # Show help
oura-scraper auth                # Interactive OAuth2 flow
oura-scraper test-api            # Test API connection
oura-scraper init-db             # Create database tables
oura-scraper init-db --print-sql # Print schema without executing
oura-scraper scrape              # Run the scraper
oura-scraper scrape --days 30    # Scrape last 30 days
```

## Environment Variables

All variables use the `OURA_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `OURA_DB_HOST` | PostgreSQL host | `localhost` |
| `OURA_DB_PORT` | PostgreSQL port | `5432` |
| `OURA_DB_NAME` | Database name | `health` |
| `OURA_DB_USER` | Database user | `health` |
| `OURA_DB_PASSWORD` | Database password | (required) |
| `OURA_CLIENT_ID` | OAuth2 client ID | (for OAuth flow) |
| `OURA_CLIENT_SECRET` | OAuth2 client secret | (for OAuth flow) |
| `OURA_ACCESS_TOKEN` | OAuth2 access token | (for bootstrap) |
| `OURA_REFRESH_TOKEN` | OAuth2 refresh token | (for bootstrap) |
| `OURA_ENCRYPTION_KEY` | Fernet key for encrypting tokens in DB | (optional) |
| `OURA_TOKEN_PATH` | Path to store OAuth tokens (local dev) | `~/.config/oura-scraper/tokens.json` |
| `OURA_SCRAPE_DAYS` | Days of data to scrape | `7` |

## Token Security

### Encryption at Rest

Tokens stored in the database can be encrypted using Fernet symmetric encryption. To enable:

1. Generate a Fernet key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Store the key securely (e.g., Azure Key Vault, AWS Secrets Manager)

3. Set the `OURA_ENCRYPTION_KEY` environment variable

When the encryption key is set, tokens are encrypted before being written to the database and decrypted when read. If no key is provided, tokens are stored in plaintext.

### Database Token Storage

The scraper stores tokens in an `oauth_tokens` table in PostgreSQL. This table is created automatically when you run `init-db`. The schema includes:

- `access_token` - The OAuth access token (encrypted if key provided)
- `refresh_token` - The OAuth refresh token (encrypted if key provided)
- `expires_at` - Token expiration timestamp
- `updated_at` - Last update timestamp

## Data Collected

The scraper collects data from all Oura API v2 endpoints:

- **Personal**: `personal_info`
- **Daily metrics**: `daily_activity`, `daily_sleep`, `daily_readiness`, `daily_stress`, `daily_spo2`
- **Sleep**: `sleep` (detailed periods), `sleep_time` (optimal bedtime)
- **Heart**: `heartrate` (5-min intervals)
- **Activity**: `workout`, `session` (meditation/breathing)
- **Other**: `enhanced_tag`, `rest_mode_period`

## Kubernetes Deployment

### Required Secrets

Create a secret with the following keys:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: oura-scraper-env
stringData:
  OURA_CLIENT_ID: "your-client-id"
  OURA_CLIENT_SECRET: "your-client-secret"
  OURA_ACCESS_TOKEN: "initial-access-token"
  OURA_REFRESH_TOKEN: "initial-refresh-token"
  OURA_ENCRYPTION_KEY: "your-fernet-key"  # Optional but recommended
```

For production, use External Secrets Operator to sync from a secrets manager.

### CronJob Configuration

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: oura-scraper
spec:
  schedule: "0 * * * *"  # Every hour
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: oura-scraper
              image: ghcr.io/mischavandenburg/oura-scraper:latest
              command: ["/app/.venv/bin/oura-scraper", "scrape"]
              envFrom:
                - secretRef:
                    name: oura-scraper-env
                - secretRef:
                    name: oura-scraper-db  # Database credentials
```

### First-Time Setup

1. Run the OAuth flow locally to get initial tokens
2. Store tokens in your secrets manager (Key Vault, etc.)
3. Deploy the CronJob
4. On first run, tokens load from env vars and get saved to database
5. Subsequent runs use database tokens (automatically refreshed)

## Development

```bash
# Lint
uv run ruff check src/

# Type check
uv run mypy src/

# Run tests
uv run pytest

# Build Docker image locally
docker build -t oura-scraper .
```

## Releases

Docker images are built and pushed to GHCR on git tags. Versioning is manual:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This triggers GitHub Actions to build and push:
- `ghcr.io/mischavandenburg/oura-scraper:v0.1.0`
- `ghcr.io/mischavandenburg/oura-scraper:latest`

## Oura API Reference

- **Base URL**: `https://api.ouraring.com/v2/usercollection/`
- **Auth**: OAuth2 with refresh tokens (single-use)
- **Rate limit**: 5,000 requests per 5-minute window
- **Scopes**: `email, personal, daily, heartrate, workout, tag, session, spo2`

## License

MIT
