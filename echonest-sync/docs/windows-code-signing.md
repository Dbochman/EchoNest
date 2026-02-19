# Windows Code Signing — Future Plan

**Status: Deferred** (cost not justified for current user base)

## Why

Without code signing, Windows shows "Windows protected your PC" (SmartScreen) on first launch. Users must click "More info" → "Run anyway". Not a blocker, but not a great first impression.

## Options

### Option A: Azure Trusted Signing (Recommended)
- **Cost**: ~$10/month (Azure subscription required)
- **Pros**: No hardware token, works from CI/CD, cloud-based
- **Cons**: Requires Azure account + identity verification (~1 week)
- **How**: Signs via Azure API using `signtool` or `az codesign` CLI
- **CI**: Add signing step to GitHub Actions Windows runner on `sync-v*` tags

### Option B: OV Code Signing Certificate
- **Cost**: ~$200-400/year (DigiCert, Sectigo, Comodo)
- **Pros**: Immediate SmartScreen trust, well-understood
- **Cons**: Since June 2023, private key must be on a **hardware USB token** (FIPS requirement). `signtool.exe` is Windows-only. Awkward for macOS-based development.
- **Workaround**: Use `osslsigncode` on macOS, or sign in CI on a Windows runner

### Option C: EV Code Signing Certificate
- **Cost**: ~$300-600/year
- **Pros**: Immediate full SmartScreen reputation (no warnings at all)
- **Cons**: Same hardware token requirement as OV, higher cost

## Implementation Plan (when ready)

1. Set up Azure Trusted Signing account
2. Complete identity verification
3. Add `sign_exe()` function to `build/windows/build_exe.py`
4. Add signing step to `.github/workflows/echonest-sync.yml` for Windows builds
5. Test that SmartScreen no longer flags the signed exe
6. Update docs to remove any SmartScreen workaround instructions

## Current Workaround

Users see SmartScreen warning on first run. Click "More info" → "Run anyway". One-time action.
