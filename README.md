# Andre

A collaborative music queue system for offices and parties. Users can search for songs, add them to a shared queue, vote on songs, and enjoy features like airhorns and "bender mode" (auto-fill).

## Features

- Spotify integration for music search and playback
- Real-time WebSocket updates for queue changes
- Voting system to promote/demote songs in queue
- "Jam" button for showing appreciation
- Airhorn sound effects
- Bender mode: auto-fills queue with recommendations when empty
- Guest login system
- Comments on songs

## Setup

### Prerequisites

- Python 3.10+
- Redis
- PostgreSQL (optional, for user data)
- Spotify Developer Account
- Google Cloud Console project (for OAuth)

### Configuration

1. Copy the example config:
   ```bash
   cp config.example.yaml local_config.yaml
   ```

2. Edit `local_config.yaml` with your credentials:

   **Required - Spotify:**
   - Create an app at https://developer.spotify.com/dashboard
   - Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
   - Add `http://localhost:5000/authentication/spotify_callback` to redirect URIs

   **Required - Google OAuth:**
   - Create credentials at https://console.cloud.google.com/apis/credentials
   - Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Add `http://localhost:5000/authentication/callback` to authorized redirect URIs

   **Email Domain Restriction:**
   ```yaml
   ALLOWED_EMAIL_DOMAINS:
     - gmail.com
     - yourdomain.com
   ```

   **Dev Mode (optional):**
   ```yaml
   DEBUG: true
   DEV_AUTH_EMAIL: "yourname@gmail.com"
   ```
   When DEBUG is true and you're on localhost, the dev email bypasses OAuth.

### Running with Docker

```bash
# Start all services
docker-compose up --build

# The app will be available at http://localhost:5000
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not using Docker)
redis-server

# Run the app
python run.py
```

## Usage

1. Visit http://localhost:5000
2. Log in with Google (must use an allowed email domain)
3. Search for songs in the Spotify tab
4. Click a result to add it to the queue
5. Vote on songs to change their position
6. Click "Jam" to show you like a song

## API Endpoints

- `GET /health` - Health check
- `GET /playing/` - Current playing song
- `GET /queue/` - Current queue
- `POST /add_song` - Add a song (email, track_uri)
- `POST /jam` - Jam a song (email, id)
- `POST /blast_airhorn` - Trigger airhorn (email, name)
- `GET /search/v2?q=` - Search Spotify

## Environment Variables

These override `local_config.yaml`:

- `REDIS_HOST` - Redis hostname (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `DEBUG` - Enable debug mode (true/false)
- `DEV_AUTH_EMAIL` - Email for dev bypass auth
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

## License

Internal use.
