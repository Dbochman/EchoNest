# echonest-sync

Desktop sync client for EchoNest. Syncs local Spotify playback to an EchoNest server via SSE events and OS-level automation (AppleScript/playerctl).

## Commands

```bash
# Install via Homebrew (macOS)
brew tap dbochman/echonest && brew install echonest-sync

# Install in dev mode (macOS)
pip install -e ".[mac]"

# Run desktop app
echonest-sync-app

# Run CLI
echonest-sync --server https://echone.st --token YOUR_TOKEN

# Run tests
SKIP_SPOTIFY_PREFETCH=1 python3 -m pytest tests/ -v
```

## Building

### macOS (.app + DMG)

Use a non-Xcode Python with working Tk support and install `.[app,mac]` into
that build environment. `/usr/local/bin/python3` was the original interpreter;
it is absent on the current Mini, where Homebrew Python 3.14 with python-tk is
used in an isolated virtualenv. Do not upgrade machine-wide Python to build.

```bash
cd echonest-sync

# With the prepared build virtualenv activated:
# 1. Build the .app bundle
python build/macos/build_app.py

# 2. Build the DMG installer
python build/macos/build_dmg.py

# Output: dist/EchoNest-Sync.dmg
```

**Rebuilding**: Prefer a fresh temporary output directory; do not delete an
existing signed app to make room for a build. `build_app.py` accepts `--distpath`
and `--workpath` (the latter also keeps the generated spec out of the checkout).
Keep the previous installed app as a rollback artifact when replacing it.

Both builders require certifi 2026.10.19 or newer and check the actual source
bundle offline. macOS checks the copied CA file before signing and derives the
app version from installed project metadata, not the historical plist template.
Run the packaged executable with `--tls-self-test` after building and installing:
it runs before GUI/config/keyring imports, makes only public TLS handshakes, and
must reject all twelve canaries while accepting both normal controls. Exit 1 is
exposure; exit 2 is inconclusive. Do not treat either as a successful test.

**Installing locally**: Open the DMG, drag to Applications, then clear quarantine:
```bash
xattr -cr "/Applications/EchoNest Sync.app"
```

### Windows (.exe)

```bash
cd echonest-sync
pip install pyinstaller
python build/windows/build_exe.py
# Output: dist/EchoNest Sync.exe
```

## Key Gotchas

- **`sys.executable` in PyInstaller**: Points to the frozen binary, NOT Python. Never pass `-m module` args to it. Use `getattr(sys, 'frozen', False)` to detect.
- **Codesign required for Keychain**: PyInstaller bundle must be ad-hoc signed or macOS Keychain rejects `keyring.set_password()`. The build script handles this automatically.
- **tkinter + rumps**: Cannot create `Tk()` when rumps owns the main thread (segfault). Use native `NSAlert` with `setAccessoryView_()` for input dialogs on macOS.
- **config DEFAULTS**: `load_config()` only reads keys present in the `DEFAULTS` dict. New config keys must be added there or they're silently dropped.
- **DMG stuck eject**: Spotlight can hold DMG volumes open. The build script adds `.metadata_never_index` and uses `-nobrowse` mount flag to prevent this.
- **Port 5000**: macOS AirPlay Receiver uses port 5000. Use port 5001 for local dev.
- **rumps quirks**: Use `quit_button=None` (rumps adds its own), `template=False` (preserves icon colors), `NSAlert` for custom dialog icons (rumps.alert uses Python rocket).

## Architecture

| File | Purpose |
|------|---------|
| `sync.py` | Core SSE listener, play/seek/pause via OS automation, override detection |
| `app.py` | Desktop launcher: keyring check → onboarding → engine thread → tray |
| `tray_mac.py` | rumps menu bar app (macOS), polls IPC events every 1s |
| `tray_win.py` | pystray tray app (Windows + Linux) |
| `config.py` | OS config dirs, keyring, save_config (strips secrets), logging |
| `ipc.py` | Thread-safe command/event queues between GUI and engine |
| `onboarding.py` | tkinter dialog, invite code → `POST /api/sync-token` |
| `link.py` | Account linking dialog (NSAlert on macOS, tkinter elsewhere) |
| `search.py` | Spotify search & add dialog (tkinter) |
| `audio.py` | Cross-platform airhorn audio caching and playback |
| `autostart.py` | LaunchAgent (macOS) / Startup folder (Windows) / XDG .desktop (Linux) |
| `updater.py` | GitHub Releases API update checker (`sync-v*` tags) |
| `player.py` | Platform player abstraction (AppleScript/playerctl/startfile) |
