# Account Linking

Account linking connects your Google identity to the sync app. This is optional — the app works fine without it — but it unlocks extra features.

## Why Link?

- **Search & Add**: The "Search & Add Song" menu item is disabled until you link your account
- **Your identity**: Songs you add through the app show your Gravatar and name instead of a generic icon
- **One-time setup**: You only need to link once; it persists across restarts and updates

## How to Link

1. Click **Link Account** in the tray menu
2. Your browser opens the EchoNest linking page — sign in with Google if prompted
3. A **6-character code** appears on the page
4. Enter the code in the dialog that appeared on your desktop
5. The menu item updates to **Linked: yourname@gmail.com**

The linking code expires after 5 minutes. If it expires, just click Link Account again to generate a new one.

## How It Works

When you link, the app receives a personal API token tied to your Google email. This token is stored securely in your system keychain alongside your main sync token. The server uses this token to attribute songs you add to your account.

## Unlinking

There's no unlink button in the app. If you need to unlink, delete the `email` entry from your config file:

- **macOS**: `~/.config/echonest-sync/config.yaml`
- **Linux**: `~/.config/echonest-sync/config.yaml`
- **Windows**: `%APPDATA%\echonest-sync\config.yaml`

Then restart the app.
