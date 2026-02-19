# Apple Developer ID — Signing & Notarization

**Status: Done** (v0.7.2, February 2026)

The macOS build is signed with `Developer ID Application: Dylan Bochman (D5VFBW83BT)` and notarized by Apple. Users get zero Gatekeeper warnings.

## Build Flow

```bash
cd ~/repos/EchoNest/echonest-sync

# Remove old build (codesigned .app has immutable files)
rm -rf "dist/EchoNest Sync.app"

# Build, sign, and notarize the .app
/usr/local/bin/python3 build/macos/build_app.py

# Build, notarize, and staple the DMG
/usr/local/bin/python3 build/macos/build_dmg.py
```

Both scripts handle signing, notarization, and stapling automatically.

Pass `--adhoc` to either script for local dev builds (skips notarization).

## Prerequisites

- **Developer ID Application certificate** in Keychain (`security find-identity -v -p codesigning`)
- **Notarization credentials** stored in Keychain:
  ```bash
  xcrun notarytool store-credentials "EchoNest-Notarize" \
    --apple-id "dylanbochman@gmail.com" --team-id "D5VFBW83BT"
  ```

## Key Files

| File | Purpose |
|------|---------|
| `build/macos/build_app.py` | PyInstaller build + recursive codesigning + notarization |
| `build/macos/build_dmg.py` | DMG creation + notarization + stapling |
| `build/macos/entitlements.plist` | Hardened runtime entitlements (network, AppleScript, dylib loading) |
| `build/macos/Info.plist` | Bundle metadata (version, LSUIElement, etc.) |
