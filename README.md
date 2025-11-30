# Oura Scraper

A Python CLI tool that scrapes health metrics from the Oura Ring API and stores them in PostgreSQL. Designed to run as a containerized CronJob on Kubernetes.

## Features

- OAuth2 authentication with automatic token refresh
- Scrapes all 17 Oura API v2 endpoints
- Upserts data to PostgreSQL (safe to re-run)
- Configurable scrape window (default: 7 days)
- Multi-stage Docker image (~50MB)
- Kubernetes-ready with environment variable configuration

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
| `OURA_ACCESS_TOKEN` | OAuth2 access token | (required) |
| `OURA_REFRESH_TOKEN` | OAuth2 refresh token | (required) |
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

## Oura API Reference

- **Base URL**: `https://api.ouraring.com/v2/usercollection/`
- **Auth**: OAuth2 with refresh tokens (single-use)
- **Rate limit**: 5,000 requests per 5-minute window
- **Scopes**: `email, personal, daily, heartrate, workout, tag, session, spo2`

## License

MIT
