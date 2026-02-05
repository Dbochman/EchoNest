# Podcast Support Implementation Plan

## Status: COMPLETE ✓

Implemented and reviewed on 2026-02-05.

---

## Overview

Add podcast/episode support to Andre, enabling users to search for and play Spotify podcasts alongside music tracks. Episodes display properly with show name (instead of artist) and correct metadata.

---

## Scope

### Implemented (V1)
- ✓ Separate podcast search (dedicated search input)
- ✓ Play episodes via Spotify
- ✓ Display episode metadata correctly (title, show name, cover art)
- ✓ Queue display with proper episode formatting
- ✓ Dynamic skip button text ("skip playing song" vs "skip playing podcast")
- ✓ One-time-per-track sync to prevent choppy audio
- ✓ Proper error handling with HTTP status checks and timeouts

### Out of Scope (V1)
- Bender auto-fill with podcasts (music-only for recommendations)
- Podcast-specific features (chapters, playback speed)
- Show browsing (only episode search)

---

## Files Modified

| File | Changes |
|------|---------|
| `db.py` | Added `get_spotify_episode()`, `_extract_images()` helper, modified `add_spotify_song()` to detect episodes via URI parsing |
| `app.py` | Added `/search/podcast` endpoint for episode-only search |
| `templates/main.html` | Added episode template, podcast search form, fixed underscore.js variable scoping with `obj.property` pattern |
| `static/js/app.js` | Added `podcast_search_submit()`, one-time sync per track, dynamic skip button text, Spotify play with `position_ms` |
| `static/css/app.css` | Added podcast search styling, `.badge-podcast` class, text overflow handling |
| `test/test_episode.py` | 9 new tests for episode URI detection, image extraction, scrobbling |

---

## Key Implementation Details

### Backend - Episode Detection

Uses explicit URI parsing instead of substring matching:
```python
uri_parts = trackid.split(':')
is_episode = len(uri_parts) >= 2 and uri_parts[1] == 'episode'
```

### Backend - API Robustness

Both `get_spotify_song()` and `get_spotify_episode()` include:
- HTTP status code validation
- Request timeout (10 seconds)
- Error response body checking
- Proper logging

### Frontend - Template Variable Scoping

Underscore.js templates use `with(obj)` blocks, so `typeof` checks don't work. Fixed with:
```html
<% if (obj.secondary_text) { %><%=obj.secondary_text%><% } else { %><%=artist%><% } %>
```

### Frontend - Audio Sync

Syncs Spotify playback only once per track to avoid choppy audio:
```javascript
if (last_synced_spotify_track != id) {
    last_synced_spotify_track = id;
    spotify_play(id, pos);
}
```

### Frontend - Position in Play Request

Uses `position_ms` in the play request body instead of separate seek call (avoids 403 errors with podcasts):
```javascript
var playData = { "uris": [id] };
if (pos && pos > 0) {
    playData.position_ms = pos * 1000;
}
```

---

## Verification Checklist

- [x] Search for podcasts in dedicated search field
- [x] Episodes appear with show name in results
- [x] Add episode to queue
- [x] Episode plays via Spotify player
- [x] Now Playing shows episode title and show name
- [x] Queue displays episode with correct metadata
- [x] Skip button shows "skip playing podcast" for episodes
- [x] "sync spotify" button works for both tracks and podcasts
- [x] No choppy audio from repeated sync calls
- [x] All 9 tests pass

---

## Code Review

Passed Codex review after fixes for:
1. Substring check bug → Explicit URI parsing
2. Double-splitting → Conditional split with colon check
3. Missing HTTP status check → Added status validation
4. No request timeout → Added 10-second timeout

---

## Post-Merge Bug Fixes

### Visual Duplicate Fix (2026-02-05)

**Issue:** When a track transitioned to now-playing, it would sometimes appear in both the "Now Playing" section AND the queue due to WebSocket timing/race conditions.

**Fix:** Added client-side filtering in `PlaylistView.render()` to exclude the now-playing track from queue display:
```javascript
var nowPlayingId = (now_playing && now_playing.get) ? now_playing.get('id') : null;
this.collection.each(function(obj){
    if (nowPlayingId && obj.get('id') === nowPlayingId) {
        return; // Skip now-playing track
    }
    // ... render queue item
});
```

Also added re-render of playlist on `now_playing_update` to apply filter immediately.

**Commit:** `7f97604`

### Spotify Unpause Fix (2026-02-05)

**Issue:** When Andre was paused and then unpaused, Spotify playback would not resume for synced clients. The `last_synced_spotify_track` check in `fix_player()` prevented re-playing the same track.

**Fix:** Added state transition detection in `now_playing_update` handler:
```javascript
var wasPaused = playerpaused;
playerpaused = data.paused;
// ...
if (wasPaused && !playerpaused && is_player) {
    resume_spotify_if_needed();
}
```

**Commit:** `1ef478f`

### Spotify 403 Error Fix (2026-02-05)

**Issue:** `resume_spotify_if_needed()` called the bare `/me/player/play` endpoint without a track URI, which requires an active Spotify device. Returns 403 Forbidden if no device is active.

**Fix:** Changed to use `spotify_play()` with the track URI and position:
```javascript
function resume_spotify_if_needed() {
    // ... guards ...
    var trackid = now_playing.get('trackid');
    var pos = now_playing.get('pos') || 0;
    if (trackid) {
        spotify_play(trackid, pos);  // Includes URI, works without active device
    }
}
```

**Commit:** `f17cccf`

---

## Rollback

Changes are additive - if issues arise:
- Comment out `/search/podcast` endpoint to disable podcast search
- Existing track functionality unchanged
- No database migrations required
