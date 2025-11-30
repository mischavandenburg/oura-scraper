# Oura Scraper

A Python CLI tool that scrapes health metrics from the Oura Ring API and stores them in PostgreSQL. Designed to run as a containerized CronJob on Kubernetes.

## Features

- OAuth2 authentication with automatic token refresh
- Scrapes all 17 Oura API v2 endpoints
- Upserts data to PostgreSQL (safe to re-run)
- Configurable scrape window (default: 7 days)
- Multi-stage Docker image (~50MB)
- Kubernetes-ready with environment variable configuration

## Getting OAuth Tokens

Before using the scraper, you need to obtain OAuth tokens from Oura:

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

For containerized deployments, extract the tokens and set them as environment variables:

```bash
export OURA_ACCESS_TOKEN=<access_token from json>
export OURA_REFRESH_TOKEN=<refresh_token from json>
```

**Note**: Refresh tokens are single-use. Each time the scraper refreshes the access token, it receives a new refresh token. The scraper handles this automatically and updates the stored tokens.

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
| `OURA_ACCESS_TOKEN` | OAuth2 access token | (for containers) |
| `OURA_REFRESH_TOKEN` | OAuth2 refresh token | (for containers) |
| `OURA_TOKEN_PATH` | Path to store OAuth tokens | `~/.config/oura-scraper/tokens.json` |
| `OURA_SCRAPE_DAYS` | Days of data to scrape | `7` |

## Data Collected

The scraper collects data from all Oura API v2 endpoints:

- **Personal**: `personal_info`
- **Daily metrics**: `daily_activity`, `daily_sleep`, `daily_readiness`, `daily_stress`, `daily_spo2`
- **Sleep**: `sleep` (detailed periods), `sleep_time` (optimal bedtime)
- **Heart**: `heartrate` (5-min intervals)
- **Activity**: `workout`, `session` (meditation/breathing)
- **Other**: `enhanced_tag`, `rest_mode_period`

## Kubernetes Deployment

Example CronJob configuration:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: oura-scraper
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: oura-scraper
              image: ghcr.io/mischavandenburg/oura-scraper:latest
              command: ["/app/.venv/bin/oura-scraper", "scrape"]
              envFrom:
                - secretRef:
                    name: oura-scraper-secrets
          restartPolicy: Never
```

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
