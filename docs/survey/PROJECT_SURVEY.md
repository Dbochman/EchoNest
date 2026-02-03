# Andre / Prosecco Project Survey

Date: 2026-02-03
Scope: Source tree survey and high-level documentation of structure and behavior.

## 1. Purpose and Summary
Andre (also called Prosecco in config and service files) is an internal “office radio” web app for queueing and playing music. It provides a real-time queue, now-playing updates, search across Spotify/YouTube/SoundCloud, and playful features like airhorns. The system is a Flask app with gevent websockets, backed primarily by Redis for state and history, plus a small Postgres demo route.

## 2. Repository Layout (Top Level)
- `app.py` — main Flask app: routes, websocket handler, auth flows, and API endpoints.
- `db.py` — core data logic: Redis-backed queue, playback state, recommendations, play logging.
- `run.py` — gevent WSGI server entrypoint (WebSocketHandler).
- `master_player.py` — entrypoint to the player loop (calls `DB.master_player()`).
- `history.py` — play history ingestion and queries (from JSON logs into Redis).
- `config.py`, `config.yaml` — configuration loader and defaults.
- `templates/` — Jinja templates (main UI, auth pages, config.js).
- `static/` — JS/CSS/assets, audio clips, fonts, gifs.
- `less/` — LESS entry (imports `spotify-glue-cat`).
- `Dockerfile`, `docker-compose.yaml` — container definitions.
- `etc/supervisor/conf.d/` and `supervise/` — supervisor config variants.
- `fabfile.py` — Fabric-based deployment automation (legacy).
- `requirements.txt` — Python dependencies (Python 2 era).
- `db_schema/` — sample SQL (not primary storage).
- `play_logs/`, `dump.rdb`, `oauth_creds/` — runtime data artifacts.
- `service-info*.yaml`, `build-info.yaml` — internal service metadata.

## 3. Runtime Architecture (High Level)
- Web app: Flask + gevent websockets.
- State: Redis is the primary store for queue, now playing, history, and misc state.
- Media sources: Spotify (Spotipy), YouTube, SoundCloud.
- Clients: Browser UI using Backbone + jQuery + underscore; websocket client for realtime updates.

## 4. Backend Details

### 4.1 Entry Points
- `run.py`: starts a gevent WSGI server with `WebSocketHandler` on port 5000.
- `master_player.py`: runs the queue/player loop via `DB.master_player()` (defined in `db.py`).

### 4.2 WebSocket Protocol (Custom)
- Incoming/outgoing messages are prefixed with a single char:
  - `"0"` for heartbeat/ping.
  - `"1"` for JSON payloads (`[eventName, ...args]`).
- `app.py` defines `WebSocketManager` and `MusicNamespace` to parse and emit events.

### 4.3 HTTP Routes (app.py)
Not exhaustive but representative list from `@app.route`:
- Auth:
  - `/login/`, `/authentication/callback` (Google OAuth2)
  - `/logout/`
  - `/spotify_connect/`, `/authentication/spotify_callback/` (Spotify OAuth)
- Queue/state:
  - `/playing/`, `/queue/`, `/queue/<int:id>`
  - `/volume/`, `/get_volume/`
  - `/api/jammit/`, `/jam`
- Search and actions:
  - `/search/v2`
  - `/add_song`
  - `/blast_airhorn`, `/airhorn_list`, `/airhorns/`
- History:
  - `/history/<int:n_plays>`
  - `/user_history/<string:userid>`
  - `/user_jam_history/<string:userid>`
- Misc:
  - `/socket/` websocket endpoint
  - `/config.js` dynamic config injection
  - `/userimg/<address>/img.png`
  - `/` main UI
  - `/z/` test Postgres query

### 4.4 Data Layer (db.py)
`DB` is the core abstraction. It initializes Redis, play history (`PlayHistory`), and Spotify clients, and provides methods for:
- Queue management, now-playing state, volume control.
- Adding songs from Spotify/YouTube/SoundCloud.
- “Bender” auto-fill logic when queue is empty.
- Airhorn tracking and limits.
- Play history logging to `play_logs/` and Redis.

### 4.5 History (history.py)
- Reads `play_logs/play_log_YYYY_MM_DD.json` files.
- Stores each play as a JSON blob in Redis sorted set `playhistory`.
- Provides per-user play and jam history queries.

## 5. Frontend Details

### 5.1 Templates
- `templates/base.html`: includes CSS/JS bundles, external SDKs, config.js, and main body block.
- `templates/main.html`: primary UI layout (now playing, queue, search, airhorns, controls).
- Other templates: guest/login helpers, welcome email, Spotify connect page.

### 5.2 JavaScript
- `static/js/app.js`:
  - Backbone models/collections/views for now playing and queue.
  - Custom websocket client with reconnect + heartbeat.
  - Search and comment UI handlers.
  - Airhorn and “other” actions.
- Additional libs: Backbone, jQuery 1.10.2, underscore, bootstrap, socket.io.

### 5.3 Styles
- `less/style.less` imports `spotify-glue-cat`.
- `static/css/app.css`, `static/css/style.css`, plus Bootstrap and Font Awesome.

## 6. Configuration

### 6.1 Config Loading
- `config.py` reads YAML files in this order:
  1. `config.yaml`
  2. `local_config.yaml` (optional, not in repo)
  3. `/etc/prosecco/local_config.yaml`
- `CONFIG_FILES` env var overrides the list.

### 6.2 Default Config (config.yaml)
- Includes numerous credentials, API keys, and secrets (Spotify, Google, YouTube, SMTP, SoundCloud, Flask secret key).
- Contains feature flags (BENDER_*), queue and airhorn limits, logging paths, hostnames.
- **Security note:** These secrets should be rotated and moved out of repo for any revival.

### 6.3 Frontend Bundles
`config.yaml` defines bundles for Flask-Assets:
- JS: `jquery-1.10.2.js`, `underscore.js`, `bootstrap.js`, `backbone.js`, `app.js`, `sc.js`
- CSS: `bootstrap.min.css`, `font-awesome.min.css`, `app.css`

## 7. Data Stores and Artifacts
- Redis is the primary store for runtime state, queue, and play history.
- Postgres is referenced only by `/z/` route and `db_schema/1.sql` sample.
- `dump.rdb` is a Redis snapshot (historical).
- `play_logs/` contains JSON logs of played tracks.
- `oauth_creds/` caches Spotify OAuth tokens.

## 8. Deployment and Operations

### 8.1 Docker
- `Dockerfile` builds on an old Ubuntu Trusty base image, installs Python 2 stack, supervisor, redis, etc.
- `docker-compose.yaml` runs Postgres and the app container, binds port 5000.

### 8.2 Supervisor
- `etc/supervisor/conf.d/prosecco.conf` defines services:
  - `prosecco_webapp`: gunicorn + geventwebsocket worker
  - `master_player`: `master_player.py`
- `supervise/` contains an older set of supervisor configs.

### 8.3 Fabric
- `fabfile.py` provisions Ubuntu hosts, installs packages, deploys from Git, and restarts supervisor.

### 8.4 Service Metadata
- `service-info.yaml`, `service-info-andre.yaml`, `service-info-highlife.yaml` are internal metadata.
- `build-info.yaml` references Spotify internal CI/CD templates.

## 9. Tests
- Minimal: `test/passing_test.py` only (no real coverage).

## 10. Risks / Modernization Notes
- Python 2 era dependencies and APIs (Flask 0.12, old gevent, old libraries).
- Secrets and keys committed in `config.yaml` and `github_deploy_key`.
- `node_modules/` is committed; no root `package.json` or frontend build pipeline.
- Mixed deployment patterns (Docker, supervisor, Fabric), likely stale.
- `gunicorn_config.py` references `socketio.sgunicorn.GeventSocketIOWorker` (old module path).

## 11. Suggested Next Steps (Optional)
If revival is planned, consider:
- Audit + rotate secrets; move to env vars or a secrets manager.
- Decide on a single deployment path (Docker vs supervisor vs Fabric).
- Modernize runtime (Python 3, updated Flask, updated dependencies).
- Add real tests, and document the queueing algorithm in code (`QUEUEING.md`).
- Verify third-party APIs (Spotify/YouTube/SoundCloud) still support current flows.

