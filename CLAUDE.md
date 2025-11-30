# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Oura API scraper that collects health metrics via OAuth2 and stores them in PostgreSQL. Designed to run as a containerized application on Kubernetes.

## Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run oura-scraper --help
uv run oura-scraper init-db --print-sql    # Print schema SQL
uv run oura-scraper init-db                 # Initialize database
uv run oura-scraper scrape                  # Run scraper

# Development
uv run ruff check src/                      # Lint
uv run mypy src/                            # Type check
uv run pytest                               # Run tests
```

## Architecture

```
src/oura_scraper/
├── __init__.py          # CLI entry point (argparse)
├── config.py            # Settings via pydantic-settings (env vars with OURA_ prefix)
├── auth.py              # OAuth2 authentication and token management
├── api_client.py        # Oura API client for all endpoints
├── scraper.py           # Main scraper orchestration
├── db/
│   ├── __init__.py
│   ├── schema.py        # SQL schema for all Oura API tables
│   └── operations.py    # Database upsert operations
```

## Environment Variables

All configuration uses `OURA_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `OURA_DB_HOST` | PostgreSQL host | localhost |
| `OURA_DB_PORT` | PostgreSQL port | 5432 |
| `OURA_DB_NAME` | Database name | health |
| `OURA_DB_USER` | Database user | health |
| `OURA_DB_PASSWORD` | Database password | (required) |
| `OURA_CLIENT_ID` | OAuth2 client ID | (required for OAuth) |
| `OURA_CLIENT_SECRET` | OAuth2 client secret | (required for OAuth) |
| `OURA_ACCESS_TOKEN` | OAuth2 access token | (required) |
| `OURA_REFRESH_TOKEN` | OAuth2 refresh token | (required) |
| `OURA_SCRAPE_DAYS` | Days to scrape | 7 |

## Database Tables

Tables created by `init-db`:
- `oura_personal_info`
- `oura_daily_activity`
- `oura_daily_sleep`
- `oura_daily_readiness`
- `oura_daily_stress`
- `oura_daily_spo2`
- `oura_sleep_data`
- `oura_sleep_time`
- `oura_heart_rate`
- `oura_workout`
- `oura_session`
- `oura_enhanced_tag`
- `oura_rest_mode_period`

## Oura API v2

**Base URL:** `https://api.ouraring.com/v2/usercollection/`

**OAuth2 URLs:**
- Authorize: `https://cloud.ouraring.com/oauth/authorize`
- Token: `https://api.ouraring.com/oauth/token`

**Important:** Refresh tokens are single-use (invalidated after use). Access tokens expire (check `expires_in`).

**Scopes:** `email, personal, daily, heartrate, workout, tag, session, spo2`

**Rate limit:** 5,000 requests per 5-minute rolling window

**All endpoints** (use `start_date` and `end_date` params, ISO 8601 YYYY-MM-DD):
- `personal_info` - User demographics
- `daily_activity` - Steps, calories, MET
- `daily_sleep` - Sleep scores
- `daily_readiness` - Readiness scores
- `daily_stress` - Stress/recovery
- `daily_spo2` - Blood oxygen
- `sleep` - Detailed sleep periods
- `sleep_time` - Optimal bedtime
- `heartrate` - 5-min HR intervals
- `workout` - Workouts
- `session` - Meditation/breathing
- `enhanced_tag` - User tags
- `rest_mode_period` - Rest mode

All paginated endpoints return `next_token` for pagination.

## Docker

```bash
# Build
docker build -t oura-scraper .

# Run
docker run --rm --env-file .env oura-scraper scrape
```

## Kubernetes

See `examples/kubernetes/` for deployment manifests.
