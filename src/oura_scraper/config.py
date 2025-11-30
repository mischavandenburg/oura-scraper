"""Configuration management via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration is done via environment variables.
    Prefix OURA_ is used for all settings.
    Loads from .env file if present.
    """

    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "health"
    db_user: str = "health"
    db_password: str = ""

    # Oura OAuth2 settings
    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""  # Can be set via env var for containerized deployments
    refresh_token: str = ""  # Can be set via env var for containerized deployments
    token_path: str = "admin/tokens/oura_tokens.json"  # Path to store OAuth tokens (fallback)

    # Scraping settings
    scrape_days: int = 7  # Number of days to scrape (default 7, can be set to 1825 for 5 years)

    model_config = SettingsConfigDict(
        env_prefix="OURA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
