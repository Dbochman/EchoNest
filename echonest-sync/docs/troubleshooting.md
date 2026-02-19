# Troubleshooting

## App Won't Connect

**Symptom**: Tray icon stays grey, status shows "Disconnected"

- Make sure you have internet access and can reach [echone.st](https://echone.st) in a browser
- The app reconnects automatically with exponential backoff — give it a minute
- If the problem persists, quit and relaunch the app

## Spotify Doesn't Play

**Symptom**: App shows "Connected" but Spotify isn't playing

- Make sure the **Spotify desktop app** is running (not the web player)
- Make sure you have a **Spotify Premium** account — Free accounts cannot be controlled via the API
- On **Linux**: Make sure `playerctl` is installed (`sudo apt install playerctl`) and Spotify appears in `playerctl -l`
- On **Windows**: Playback control is limited — the app can open tracks but cannot seek to the correct position

## Sync Paused Unexpectedly

**Symptom**: Icon turns yellow/brown, menu shows "Paused"

This usually means override detection kicked in — the app detected that you manually changed the track in Spotify. Click **Resume Sync** in the tray menu to restart syncing.

## macOS Gatekeeper Warning (v0.7.1 and earlier)

**Symptom**: "EchoNest Sync can't be opened because Apple cannot check it for malicious software"

This was fixed in v0.7.2 — the app is now signed with an Apple Developer ID and notarized. Update to the latest release to resolve this.

If you're on an older version, you can work around it by right-clicking the app and choosing **Open**, or running `xattr -cr "/Applications/EchoNest Sync.app"` in Terminal.

## macOS Keychain Permission Prompt

**Symptom**: macOS asks "echonest-sync wants to use your keychain" on every launch

Click **Always Allow** to grant permanent access. If the prompt keeps appearing, the app binary may have been modified — reinstall from the DMG.

## Search & Add Is Greyed Out

**Symptom**: "Search & Add Song" menu item is disabled

You need to [link your account](./account-linking.md) first. Click **Link Account** in the tray menu and follow the steps.

## Linking Code Expired

**Symptom**: "Invalid code" error when entering the 6-character code

Linking codes expire after 5 minutes. Click **Link Account** again to generate a fresh code.

## Port 5000 Conflict on macOS

**Symptom**: Can't run the EchoNest server locally

macOS Monterey and later use port 5000 for AirPlay Receiver. Either:

- Disable AirPlay Receiver in **System Settings > General > AirDrop & Handoff**, or
- Run the server on port 5001 instead

## Audio Doesn't Play (Airhorns)

**Symptom**: Airhorns are enabled but no sound plays

- **macOS**: Should work out of the box (`afplay` is built-in). Check your volume.
- **Linux**: Requires PulseAudio (`paplay`). If unavailable, falls back to `aplay`.
- **Windows**: Requires `ffplay` (from FFmpeg) or `mpv`. Without either, only `.wav` files play via the built-in `winsound` module.

## App Doesn't Start at Login

**Symptom**: "Start at Login" is checked but the app doesn't launch on boot

- **macOS**: Check that `~/Library/LaunchAgents/st.echone.sync.plist` exists. If using a pip install, make sure `echonest-sync-app` is on your PATH.
- **Windows**: Check the Startup folder (`shell:startup` in Run dialog) for the shortcut.
- **Linux**: Check `~/.config/autostart/echonest-sync.desktop` exists.

## Resetting the App

If you need to start fresh:

1. Quit EchoNest Sync
2. Delete the config file:
   - **macOS / Linux**: `rm -rf ~/.config/echonest-sync/`
   - **Windows**: Delete `%APPDATA%\echonest-sync\`
3. Remove the keychain entry:
   - **macOS**: Open Keychain Access, search for "echonest", and delete the entry
   - **Windows**: Use Credential Manager to find and remove the "echonest-sync" credential
   - **Linux**: `keyring del echonest-sync token`
4. Relaunch the app — onboarding will run again
