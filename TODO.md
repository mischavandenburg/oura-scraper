# TODO - Oura Scraper Development

## Completed

- [x] Research UV best practices (src layout, `uv init --package`)
- [x] Research Oura API v2 (OAuth2 flow, all endpoints, rate limits)
- [x] Analyze existing database schema in `health` database
- [x] Initialize UV project with src layout
- [x] Create `pyproject.toml` with dependencies (httpx, psycopg, pydantic, pydantic-settings)
- [x] Set up dev tools (ruff, mypy, pytest)
- [x] Create config module with environment variable settings
- [x] Design complete database schema for all 17 Oura API endpoints
- [x] Create CLI with `init-db` and `scrape` commands
- [x] Linting and type checking pass

## Next Steps

### 1. OAuth2 Authentication Module
Create `src/oura_scraper/auth.py`:
- [ ] Implement token refresh flow (refresh tokens are single-use!)
- [ ] Store new tokens after refresh (needs strategy: env vars? file? database?)
- [ ] Handle token expiration (`expires_in` field)
- [ ] Create OAuth2 authorization flow for initial token acquisition
- [ ] Consider: How to handle initial OAuth2 authorization (browser redirect flow)

**OAuth2 Flow Notes:**
1. User authorizes at `https://cloud.ouraring.com/oauth/authorize?client_id=XXX&redirect_uri=XXX&response_type=code&scope=XXX`
2. Oura redirects to your `redirect_uri` with `?code=XXX`
3. Exchange code for tokens: POST to `https://api.ouraring.com/oauth/token`
4. Refresh: POST with `grant_type=refresh_token` - **new refresh token returned, old one invalidated**

### 2. API Client Module
Create `src/oura_scraper/api/`:
- [ ] Create base client with httpx (async)
- [ ] Add authentication header injection
- [ ] Implement rate limiting (5000 req / 5 min)
- [ ] Handle pagination (`next_token`)
- [ ] Create endpoint-specific methods for all 17 endpoints
- [ ] Add retry logic with exponential backoff

### 3. Data Models (Pydantic)
Create `src/oura_scraper/models/`:
- [ ] Define Pydantic models for all API response types
- [ ] Match models to database schema
- [ ] Handle optional fields and nullable values

### 4. Database Operations
Create `src/oura_scraper/db/operations.py`:
- [ ] Upsert functions for each table (ON CONFLICT)
- [ ] Batch insert for efficiency
- [ ] Transaction management
- [ ] Query functions for checking existing data (avoid re-scraping)

### 5. Scraper Implementation
Implement in `src/oura_scraper/__init__.py` or new module:
- [ ] Calculate date range from `OURA_SCRAPE_DAYS`
- [ ] Fetch data from all endpoints
- [ ] Transform API responses to database models
- [ ] Insert/update database
- [ ] Handle incremental scraping (only fetch new data)
- [ ] Progress logging

### 6. Testing
- [ ] Unit tests for auth module
- [ ] Unit tests for API client (mock responses)
- [ ] Integration tests against real database (optional)
- [ ] Test fixtures with sample API responses

### 7. Containerization
- [ ] Create `Dockerfile`
- [ ] Create Kubernetes manifests (Deployment, CronJob, Secret, ConfigMap)
- [ ] Set up as CronJob for periodic scraping
- [ ] Configure external-secrets for OAuth tokens from Azure Key Vault

### 8. Grafana Dashboards
- [ ] Design queries for common metrics
- [ ] Create dashboard JSON
- [ ] Consider: provisioning via ConfigMap

## Questions to Resolve

1. **Token storage:** Where to persist refreshed OAuth tokens?
   - Environment variable (requires restart/redeploy)
   - File (needs persistent volume)
   - Database table (adds complexity but most robust)
   - Azure Key Vault via external-secrets (most secure)

2. **Initial OAuth setup:** How to do first-time authorization?
   - One-time CLI command that opens browser?
   - Separate setup script?
   - Manual process documented in README?

3. **Scraping strategy:**
   - Full historical backfill (5 years) - run once with high `OURA_SCRAPE_DAYS`
   - Daily incremental - CronJob with `OURA_SCRAPE_DAYS=2` (overlap for safety)

4. **Error handling:**
   - What to do if OAuth refresh fails? (tokens expired, need re-auth)
   - Partial failures (some endpoints succeed, others fail)?

## File Structure (Planned)

```
src/oura_scraper/
├── __init__.py          # CLI entry point ✓
├── config.py            # Environment settings ✓
├── auth.py              # OAuth2 token management
├── api/
│   ├── __init__.py
│   ├── client.py        # Base HTTP client
│   └── endpoints.py     # Endpoint-specific methods
├── models/
│   ├── __init__.py
│   └── oura.py          # Pydantic models for API responses
├── db/
│   ├── __init__.py      # ✓
│   ├── schema.py        # SQL schema ✓
│   └── operations.py    # CRUD operations
└── scraper.py           # Main scraping logic
```

## Database Credentials

For development, use kubectl port-forward or direct connection:
```bash
# Port forward (run in separate terminal)
kubectl port-forward -n health-api svc/health-db-lb 5432:5432

# Then set env vars
export OURA_DB_HOST=localhost
export OURA_DB_PORT=5432
export OURA_DB_NAME=health
export OURA_DB_USER=health
export OURA_DB_PASSWORD=Z9inwimNF1UupqDF
```

Or connect via LoadBalancer IP (192.168.100.212) if on same network.
