"""PyInstaller build script for macOS .app bundle.

Usage:
    cd echonest-sync
    pip install pyinstaller
    python build/macos/build_app.py

Produces: dist/EchoNest Sync.app
"""

import argparse
from importlib.metadata import version
import os
import plistlib
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))


def build(distpath=None, workpath=None):
    distpath = distpath or os.path.join(ROOT, "dist")
    preflight = os.path.join(ROOT, "tools", "check_tls_bundle.py")
    subprocess.check_call([sys.executable, preflight])
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "EchoNest Sync",
        "--windowed",                    # .app bundle, no console
        "--onedir",                      # directory bundle (smaller, faster startup)
        "--noconfirm",                   # overwrite without asking

        # macOS-specific
        "--osx-bundle-identifier", "st.echone.sync",

        # App icon
        "--icon", os.path.join(ROOT, "resources", "icon.icns"),

        # Resources
        "--add-data", os.path.join(ROOT, "resources") + ":resources",

        # Hidden imports that PyInstaller may miss
        "--hidden-import", "rumps",
        "--hidden-import", "keyring.backends.macOS",
        "--hidden-import", "keyring.backends.SecretService",

        # Hidden imports for the app modules (relative imports in the package)
        "--hidden-import", "echonest_sync.config",
        "--hidden-import", "echonest_sync.ipc",
        "--hidden-import", "echonest_sync.player",
        "--hidden-import", "echonest_sync.sync",
        "--hidden-import", "echonest_sync.app",
        "--hidden-import", "echonest_sync.tray_mac",
        "--hidden-import", "echonest_sync.onboarding",
        "--hidden-import", "echonest_sync.autostart",

        # Entry point (uses absolute imports, not relative)
        os.path.join(ROOT, "src", "echonest_sync", "__main__.py"),
    ]
    cmd.extend(["--distpath", distpath])
    if workpath:
        cmd.extend(["--workpath", workpath, "--specpath", workpath])

    print("Building macOS .app bundle...")
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    # Replace PyInstaller's generated Info.plist with our custom one
    app_path = os.path.join(distpath, "EchoNest Sync.app")
    subprocess.check_call([
        sys.executable, preflight, "--ca-file",
        os.path.join(app_path, "Contents", "Resources", "certifi", "cacert.pem"),
    ])
    app_plist = os.path.join(app_path, "Contents", "Info.plist")
    custom_plist = os.path.join(BUILD_DIR, "Info.plist")
    if os.path.exists(custom_plist):
        print(f"Replacing Info.plist with {custom_plist}")
        shutil.copy2(custom_plist, app_plist)

    # The historical template still says 0.2.1. Use installed project metadata,
    # so a rebuilt 0.7.0 app cannot advertise itself as an older installation.
    with open(app_plist, "rb") as stream:
        info = plistlib.load(stream)
    info["CFBundleVersion"] = info["CFBundleShortVersionString"] = version("echonest-sync")
    with open(app_plist, "wb") as stream:
        plistlib.dump(info, stream)

    # Ad-hoc codesign so macOS Keychain allows keyring access
    print("Ad-hoc signing .app bundle...")
    subprocess.check_call([
        "codesign", "--force", "--deep", "--sign", "-", app_path,
    ])

    print("\nBuild complete: " + app_path)
    print("To create a DMG:")
    print("  python build/macos/build_dmg.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distpath")
    parser.add_argument("--workpath")
    args = parser.parse_args()
    build(args.distpath, args.workpath)
