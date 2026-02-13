# echonest-sync

CLI agent that syncs your local Spotify with an EchoNest server. No Spotify OAuth needed — uses OS-level automation (AppleScript on macOS, playerctl on Linux) to control your Spotify app directly.

## Install

```bash
cd echonest-sync
pip install -e .
```

## Usage

```bash
# Basic usage
echonest-sync --server https://echone.st --token YOUR_API_TOKEN

# With debug logging
echonest-sync -s https://echone.st -t YOUR_API_TOKEN -v

# Custom drift threshold (default 3 seconds)
echonest-sync -s https://echone.st -t YOUR_API_TOKEN -d 5
```

## Config file

Create `~/.echonest-sync.yaml`:

```yaml
server: https://echone.st
token: YOUR_API_TOKEN
drift_threshold: 3
```

Then just run:

```bash
echonest-sync
```

Environment variables also work: `ECHONEST_SERVER`, `ECHONEST_TOKEN`, `ECHONEST_DRIFT_THRESHOLD`.

Precedence: CLI args > env vars > config file.

## Prerequisites

- **Spotify desktop app** must be running
- **macOS**: No extra dependencies (uses AppleScript)
- **Linux**: Install `playerctl` (`sudo apt install playerctl`)
- **Windows**: Limited support (can open tracks but cannot seek)

## How it works

1. Connects to the EchoNest SSE event stream (`/api/events`)
2. On `now_playing` events: plays the same track on your local Spotify and seeks to the correct position
3. On `player_position` events: corrects drift if your local playback drifts more than the threshold
4. Handles pause/resume automatically
5. Reconnects with exponential backoff on connection loss
