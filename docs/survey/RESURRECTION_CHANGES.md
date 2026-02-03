# Resurrection Changes (SSO Removal + Python 3 Port)

Date: 2026-02-03

## Summary
This document records the changes made to resurrect Andre/Prosecco with a Python 3 baseline, remove SSO header auth, and keep Google OAuth as the primary login. A dev-only bypass was added for local testing, plus container/runtime updates.

## Auth Changes
- Removed header-based SSO (`sso-mail`, `sso-givenname`, `sso-surname`) and `useremail` query fallback.
- Unauthenticated requests now redirect to `/login/` (except existing `SAFE_PATHS`).
- Added **dev-only bypass**:
  - Enabled when `DEBUG=True` **and** `DEV_AUTH_EMAIL` is set.
  - Only applies on localhost.
  - Sets `session['email']` and `session['fullname']='Dev User'`.

Files:
- `app.py`
- `config.py`
- `config.yaml`

## Python 3 Compatibility
- Updated Python 2 print statements.
- Replaced `urllib`/`urllib2` usage with `urllib.parse.urlencode`.
- Replaced `flask.ext.assets` with `flask_assets`.
- Converted `map()` calls to explicit loops where needed.
- Replaced `basestring` with `str`.
- Replaced `unicode` with `str`.

Files:
- `app.py`
- `db.py`
- `history.py`
- `run.py`
- `config.py`
- `dominator.py`

## Redis + Pickle Handling
- Redis now uses `decode_responses=True` to normalize string handling.
- Added base64-wrapped pickle helpers to avoid bytes/str errors:
  - `MISC|bender_streak_start`
  - `MISC|current-done`
  - `MISC|player-now`
  - guest login expiry
- Updated all read/write call sites to use safe wrappers.

Files:
- `db.py`
- `app.py` (websocket pubsub uses same Redis host/port)

## Dependency and Runtime Updates
- Updated `requirements.txt` to Python 3 compatible package versions.
- Added `pytest` and `simplejson`.
- Dropped outdated/unused deps.

Files:
- `requirements.txt`

## Containerization
- Dockerfile updated to `python:3.10-slim` with modern build deps.
- Compose adds Redis service and env vars for Redis + dev auth.
- Postgres service retained for `/z/` route compatibility.

Files:
- `Dockerfile`
- `docker-compose.yaml`

## Documentation + Examples
- Added setup + dev bypass instructions in `README.md`.
- Added `config.example.yaml` with placeholder secrets.
- Added `.gitignore` for local config, oauth cache, logs, and node_modules.

Files:
- `README.md`
- `config.example.yaml`
- `.gitignore`

## Tests
Added minimal auth tests:
- Unauthenticated `/` redirects to `/login/`.
- Dev bypass grants access and sets session.

Files:
- `test/test_auth.py`

## How to Verify
1. **Compose:** `docker-compose up --build`
2. **Dev bypass:** set `DEBUG=True` and `DEV_AUTH_EMAIL=dev@example.com`
3. **Tests:** `SKIP_SPOTIFY_PREFETCH=1 pytest`

## Notable Behavior Changes
- SSO headers are ignored.
- Dev bypass is **opt-in** and only on localhost.
- Redis is configurable via `REDIS_HOST` / `REDIS_PORT`.
