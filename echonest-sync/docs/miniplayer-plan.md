# Winamp-Inspired Mini Player for EchoNest Sync

## Context

The EchoNest desktop sync app currently uses a system tray menu (rumps on macOS, pystray on Windows/Linux) to show now-playing info as text. A Winamp-inspired mini player adds an optional always-on-top floating window showing album art, track info, and a progress bar — a fun nostalgic alternative to the menu interface.

### Prior Art: Spotiamp

[Spotiamp](https://github.com/tedsteen/Spotiamp) is a full standalone Spotify client built with Tauri 2 (Rust) + Svelte 5 that pixel-perfectly recreates Winamp 2.91 using original `.BMP` sprite sheets and `.CUR` cursor files. Key differences from our approach:

- **Spotiamp is a full player** (librespot audio decoding, local playback) — we're a companion display widget for an existing server
- **Spotiamp uses Tauri/webview** (~20MB+ binary, Rust build toolchain) — we use tkinter (stdlib, zero new deps)
- **Spotiamp has 29 skin bitmap assets** with pixel-exact CSS positioning — we use a simple dark theme with album art

**Borrowed from Spotiamp:**
- **Paused time blink**: When paused, Winamp blinks the time display on/off every 1s (`numberDisplayHidden = !numberDisplayHidden`). We add this to our 250ms timer — cheap nostalgia win.
- **Optimistic UI on button clicks**: Set visual state immediately, then send the command. Spotiamp does `playerState = "paused"` before `invoke("pause")` "to make the UI a bit snappier." We do similar with button disable + immediate icon swap.
- **Client-side seek interpolation**: Spotiamp uses `seekPosition += 1000` every 1s between server `PositionCorrection` events. Same pattern as our 250ms interpolation timer, just coarser.

**Not borrowed (wrong fit):**
- Full skin system (sprite sheets, custom cursors) — massive surface area for a companion widget
- Tauri/webview — new dependency + build pipeline, doesn't match existing patterns
- Real-time FFT visualizer — requires audio sink access we don't have
- Double-size zoom mode — unnecessary for our use case

## Approach

- **Framework**: tkinter (stdlib, cross-platform, already used for search/onboarding)
- **Activation**: "Mini Player" toggle in tray menu
- **Subprocess model**: Like the search dialog, runs as a separate process to avoid tkinter + rumps segfault on macOS
- **IPC**: stdin/stdout newline-delimited JSON between tray (parent) and mini player (child)

## Design

Compact borderless window (~350x120px), always-on-top, dark theme:

```
┌──────────────────────────────────────────┐
│ ┌────────┐  Song Title (bold 12pt)       │
│ │ Album  │  Artist Name (10pt)           │
│ │  Art   │  ⏸ ━━━━━━━━━━━━━━━━ 2:14/3:45│
│ │ 80x80  │                               │
│ └────────┘                               │
└──────────────────────────────────────────┘
```

- **Colors**: Background `#1a1a1a`, white text, progress bar fill `#28d7fe` (Winamp cyan accent)
- **Album art**: 80x80px from `big_img` URL. Use **Pillow** (`PIL.Image`) to load JPEG data (Pillow is already in `[app]` extra deps), resize to 80x80, convert to `ImageTk.PhotoImage`. Cache downloaded images to disk under `get_config_dir() / "art_cache"` keyed by URL hash. Grey `#333333` placeholder on fetch failure or before first track.
- **Initial state**: Before the first track event, show grey placeholder art + "No track playing" / empty artist / zeroed progress bar. This is the deterministic cold-start UI.
- **Progress bar**: Canvas rectangle, updates via 250ms interpolation timer between server position events (freeze when paused)
- **Paused time blink**: When paused, toggle the time label visibility every 1s (à la Winamp). Implemented in the 250ms timer with a modulo counter.
- **Play/pause**: Unicode `▶`/`⏸` button. Optimistic UI — swap icon immediately on click, then send command to parent. Brief disable after click to prevent spam.
- **Draggable**: Click-and-drag anywhere on window background (store offsets, update geometry)
- **Position persistence**: Save/load `miniplayer_x`/`miniplayer_y` via existing `save_config()`/`load_config()` in `config.py`. Clamp to visible screen on restore.

## IPC Protocol

**Parent (tray) → Child (stdin), JSON lines:**
- `{"type": "track", "title": "...", "artist": "...", "img": "...", "big_img": "...", "duration": 180, "paused": false}`
- `{"type": "position", "pos": 134.5}` (debounced to ~1 Hz)
- `{"type": "paused", "paused": true}`
- `{"type": "quit"}`

**Child → Parent (stdout), JSON lines:**
- `{"type": "command", "cmd": "pause"}` / `{"type": "command", "cmd": "resume"}`
- `{"type": "closed"}` (user closed window)

Parent buffers latest track + paused state so a newly spawned mini player initializes immediately.

## Files to Create/Modify

### 1. `sync.py` (~line 210) — Enrich events

Add `img`, `big_img`, `duration` to `track_changed` emission:
```python
self._emit("track_changed", uri=uri, title=title, artist=artist,
           img=data.get("img", ""), big_img=data.get("big_img", ""),
           duration=data.get("duration", 0))
```

Add `player_position` IPC event in `_handle_player_position()`:
```python
self._emit("player_position", pos=server_pos)
```

### 2. `config.py` — Add DEFAULTS

Add `miniplayer_x: None` and `miniplayer_y: None` to the DEFAULTS dict.

### 3. `ipc.py` — Update docstring

Add `player_position` to the Event docstring.

### 4. `miniplayer.py` (NEW, ~280 lines) — The mini player window

- `MiniPlayerWindow` class with tkinter root
- `overrideredirect(True)` borderless, `wm_attributes('-topmost', True)` always-on-top
- Background stdin reader thread → `root.after()` to post to main thread
- **Album art pipeline**: Background thread fetches URL via `requests.get()` → save to `get_config_dir() / "art_cache" / {sha256(url).hex()[:16]}.jpg` → load with `PIL.Image.open()` → resize to 80x80 → pass bytes to main thread → create `ImageTk.PhotoImage` on main thread and store ref on `self._art_photo` to prevent GC
- **Initial render**: Grey placeholder (`#333333` 80x80 rectangle) + "No track playing" title + empty artist + zeroed progress bar
- **Progress bar**: Canvas with 250ms interpolation timer (freeze when paused)
- **Paused time blink**: 250ms timer increments a counter; when paused, toggle time label visibility every 4 ticks (~1s). When resumed, ensure time label is visible.
- **Optimistic play/pause**: Swap `▶`/`⏸` icon immediately on click before sending IPC command
- Draggable via `<Button-1>`/`<B1-Motion>` binds
- **Config persistence**: Use `load_config()` to read `miniplayer_x`/`miniplayer_y` on startup; use `save_config()` to persist on close. Import from `.config` module.
- On close: save position, write `{"type": "closed"}` to stdout, `root.destroy()`
- On stdin EOF or broken pipe: cleanup and exit gracefully
- Also runnable standalone via `if __name__ == "__main__"` for debugging

### 5. `app.py` — Add `--miniplayer` flag

```python
if "--miniplayer" in sys.argv:
    from .miniplayer import MiniPlayerWindow
    MiniPlayerWindow().run()
    return
```

### 6. `tray_mac.py` — Menu item + subprocess management

- Add `self.miniplayer_item = rumps.MenuItem("Mini Player", callback=self.toggle_miniplayer)` to menu
- `self._miniplayer_proc = None`, `self._miniplayer_state = {}` (buffered track/paused state)
- **Subprocess spawn**: Reuse the same frozen-detection pattern from `search.py:launch_search()` — `getattr(sys, 'frozen', False)` to decide between `[sys.executable, "--miniplayer"]` (frozen) and `[sys.executable, "-m", "echonest_sync.miniplayer"]` (pip install). Use `subprocess.Popen` with `stdin=PIPE, stdout=PIPE`.
- Forward `track_changed`, `player_position`, `player_paused` events to child stdin as JSON lines
- Read child stdout via rumps `@rumps.timer` (reuse existing 1s poll timer); handle `command` (call existing `channel.send_command("pause")`/`channel.send_command("resume")`), `closed` (uncheck menu, null proc)
- Log spawn failures, IPC decode errors, unexpected exit codes

### 7. `tray_win.py` — Same integration (covers both Windows and Linux)

`tray_win.py` handles **both Windows and Linux** (there is no separate `tray_linux.py`). Mirror tray_mac subprocess management. Read stdout via dedicated thread + queue (pystray has no built-in timers).

## Implementation Order

1. `sync.py` — Enrich events (small, no risk)
2. `config.py` — Add defaults
3. `ipc.py` — Docstring update
4. `miniplayer.py` — Build the window (bulk of work)
5. `app.py` — Add flag handling
6. `tray_mac.py` — Tray integration
7. `tray_win.py` — Tray integration

## Error Handling

- **Album art fetch failure**: Grey placeholder, single retry for transient errors
- **Broken pipe / stdin EOF**: Mini player exits gracefully with `root.destroy()`
- **Child unexpected exit**: Parent logs exit code, unchecks menu item, nulls proc reference
- **IPC decode errors**: Parent logs and tears down child

## Verification

1. **Manual macOS test**:
   ```bash
   cd echonest-sync && pip install -e ".[app,mac]"
   echonest-sync-app
   # Toggle "Mini Player" from tray → window with art, title, progress
   # Verify: progress animates, pause/resume works, draggable, position persists
   # Verify: time blinks when paused (à la Winamp)
   ```

2. **Subprocess smoke test**:
   ```bash
   echo '{"type":"track","title":"Test Song","artist":"Test Artist","big_img":"","duration":200,"paused":false}' | python -m echonest_sync.miniplayer
   ```

3. **Regression tests**:
   ```bash
   cd echonest-sync && SKIP_SPOTIFY_PREFETCH=1 python3 -m pytest tests/ -v
   ```

4. **Optional**: Add unit test for `track_changed` emission (mock `_emit`, assert new fields present)
