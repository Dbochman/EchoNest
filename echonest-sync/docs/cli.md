# CLI Usage

The CLI is an alternative to the desktop app for headless setups, scripts, or users who prefer the terminal.

## Installation

The CLI is only available when installing from source via pip — it is not included in the `.dmg` or `.exe` downloads (those bundle the desktop app only).

```bash
cd echonest-sync

# macOS
pip install -e ".[mac]"

# Windows / Linux
pip install -e .
```

This installs both `echonest-sync` (CLI) and `echonest-sync-app` (desktop app) as commands.

## Quick Start

```bash
echonest-sync --server https://echone.st --token YOUR_API_TOKEN
```

## Options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--server URL` | `-s` | EchoNest server URL | (required) |
| `--token TOKEN` | `-t` | API token | (from keyring/config) |
| `--drift-threshold N` | `-d` | Seconds of drift before seeking | `3` |
| `--verbose` | `-v` | Enable debug logging | off |

## Config File

Instead of passing flags every time, create a config file:

**Location**: `~/.echonest-sync.yaml` or `~/.config/echonest-sync/config.yaml`

```yaml
server: https://echone.st
token: YOUR_API_TOKEN
drift_threshold: 3
```

Then run without arguments:

```bash
echonest-sync
```

## Environment Variables

You can also configure via environment variables:

| Variable | Maps To |
|----------|---------|
| `ECHONEST_SERVER` | `--server` |
| `ECHONEST_TOKEN` | `--token` |
| `ECHONEST_DRIFT_THRESHOLD` | `--drift-threshold` |

## Precedence

When the same setting is specified in multiple places, the highest-priority source wins:

1. CLI arguments (highest)
2. Environment variables
3. Config file
4. System keychain (lowest — token only)

## Examples

```bash
# Connect with debug logging
echonest-sync -s https://echone.st -t YOUR_TOKEN -v

# Use environment variables
export ECHONEST_SERVER=https://echone.st
export ECHONEST_TOKEN=YOUR_TOKEN
echonest-sync

# Custom drift threshold (5 seconds)
echonest-sync -s https://echone.st -t YOUR_TOKEN -d 5
```

## Differences from the Desktop App

The CLI does not include:

- Tray icon or menu
- Onboarding dialog (you must provide server and token manually)
- Account linking or Search & Add
- Airhorn audio playback
- Autostart management
- Update checking

It does include the core sync features: playback control, drift correction, override detection, and automatic reconnection.
