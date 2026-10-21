# echonest-sync

Desktop agent that syncs your local Spotify with an EchoNest server. No Spotify OAuth needed — uses OS-level automation (AppleScript on macOS, playerctl on Linux) to control your Spotify app directly.

## Desktop App (Recommended)

Download from [Releases](https://github.com/Dbochman/EchoNest/releases) or install from source:

```bash
cd echonest-sync

# macOS
pip install -e ".[mac]"

# Windows / Linux
pip install -e .
```

Launch the desktop app:

```bash
echonest-sync-app
```

On first launch, an onboarding dialog auto-connects to EchoNest — no invite code or configuration needed. A tray icon appears with playback status and controls.

### Account Linking

Link your Google account so songs you add show your avatar instead of a generic icon:

1. Click **Link Account** in the tray menu
2. Sign in with Google at the page that opens
3. Enter the 6-character code in the dialog
4. Songs you search & add will now show your Gravatar

Linking is optional — the app works without it.

### Tray Menu

- **Track info** — click to foreground Spotify
- **Up Next** — submenu showing upcoming queue
- **Open EchoNest** — opens echone.st in your browser
- **Pause / Resume Sync** — temporarily stop syncing (also pauses local Spotify)
- **Mini Player** — toggle the floating always-on-top mini player (album art, progress bar, play/pause, airhorn toggle, up next)
- **Airhorns: On/Off** — toggle airhorn sound playback
- **Search & Add Song** — search Spotify and add to queue (requires linked account)
- **Link Account** — link your Google account for identity
- **Check for Updates** — check GitHub for new releases
- **Start at Login** — enable/disable autostart
- **Quit**

### Tray Icon Colors

| Icon | Meaning |
|------|---------|
| 🪺 Green | Connected and syncing |
| 🪹 Brown | Connected but paused |
| 🪹 Grey | Connecting / not connected |

## CLI

For headless or scripted use:

```bash
# Basic usage
echonest-sync --server https://echone.st --token YOUR_API_TOKEN

# With debug logging
echonest-sync -s https://echone.st -t YOUR_API_TOKEN -v

# Custom drift threshold (default 3 seconds)
echonest-sync -s https://echone.st -t YOUR_API_TOKEN -d 5
```

### Config file

Create `~/.echonest-sync.yaml` or `~/.config/echonest-sync/config.yaml`:

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

Precedence: CLI args > env vars > config file > keyring.

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
5. Detects manual playback overrides and auto-pauses sync
6. Reconnects with exponential backoff on connection loss

## Building

### Certificate trust in packaged apps

The desktop package requires `certifi>=2026.10.19` following the
[eMudhra incident](https://github.com/certifi/python-certifi/releases/tag/2026.10.19).
Install the package's dependencies into the build interpreter before packaging.
Both builders run an offline check of the certifi release and actual CA file;
macOS also checks the copied bundle before signing. This check rejects known
incident-excluded roots, but is not a general-purpose revocation service.

Updating system Python or Homebrew does **not** replace the CA file inside an
already installed `.app` or `.exe`. Rebuild and reinstall the app, retain its
existing user configuration, and test the packaged bundle against all incident
canaries plus normal controls before treating that installation as remediated.
Do not replace files inside a signed app in place or disable TLS verification.
Changing this source does not repair an existing installation. The packaged
executable supports a credential-free diagnostic, before loading GUI/config or
Keychain code:

```bash
"/Applications/EchoNest Sync.app/Contents/MacOS/EchoNest Sync" --tls-self-test
```

It makes TLS handshakes only (no HTTP requests) to twelve public incident
canaries and two normal controls. Exit 0 means expected rejection plus working
controls; 1 means observed exposure; 2 means inconclusive. Run on an available
network. It does not start playback, register startup items, or modify trust.

For isolated macOS builds, pass `--distpath` and `--workpath` pointing inside a
fresh temporary directory. The app version is taken from installed project
metadata rather than the historical plist template. A non-Xcode Python with
Tk support is required; `/usr/local/bin/python3` below is a historical example,
not a required location. The October 2026 Mini build uses Homebrew Python 3.14.

### macOS (.app bundle)

```bash
cd echonest-sync
pip install pyinstaller
/usr/local/bin/python3 build/macos/build_app.py
# Output: dist/EchoNest Sync.app
```

### Windows (.exe)

```bash
cd echonest-sync
pip install pyinstaller
python build/windows/build_exe.py
# Output: dist/EchoNest Sync.exe
```
