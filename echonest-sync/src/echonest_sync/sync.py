"""SSE subscription loop + state machine for syncing local Spotify."""

import json
import logging
import time
from datetime import datetime

import requests
import sseclient

log = logging.getLogger(__name__)


def _elapsed_seconds(starttime_str, now_str):
    """Seconds elapsed between two server timestamps (same clock, no TZ needed)."""
    start = datetime.fromisoformat(starttime_str)
    now = datetime.fromisoformat(now_str)
    return max(0, (now - start).total_seconds())


class SyncAgent:
    def __init__(self, server, token, player, drift_threshold=3):
        self.server = server.rstrip("/")
        self.token = token
        self.player = player
        self.drift_threshold = drift_threshold

        # State
        self.current_track_uri = None
        self.current_src = None
        self.paused = False

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _initial_sync(self):
        """GET /api/playing to sync immediately on connect."""
        try:
            resp = requests.get(
                f"{self.server}/api/playing",
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            log.debug("Initial sync data: %s", data)
            self._handle_now_playing(data)
        except Exception as e:
            log.warning("Initial sync failed: %s", e)

    def _handle_now_playing(self, data):
        """Process a now_playing event or /api/playing response."""
        src = data.get("src", "")
        trackid = data.get("trackid", "")
        starttime = data.get("starttime", "")
        server_now = data.get("now", "")
        is_paused = bool(data.get("paused"))

        if not trackid:
            log.debug("No track playing")
            self.current_track_uri = None
            self.current_src = None
            return

        if src != "spotify":
            log.info("Non-Spotify track (%s) — skipping local control", src)
            self.current_track_uri = None
            self.current_src = src
            return

        uri = f"spotify:track:{trackid}"
        self.current_src = src

        if uri != self.current_track_uri:
            log.info("Now playing: %s", uri)
            self.player.play_track(uri)
            self.current_track_uri = uri

            if starttime and server_now:
                elapsed = _elapsed_seconds(starttime, server_now)
                if elapsed > 1:
                    log.debug("Seeking to %.1fs (elapsed since start)", elapsed)
                    # Small delay to let Spotify load the track
                    time.sleep(0.5)
                    self.player.seek_to(elapsed)

        # Handle pause/resume
        if is_paused and not self.paused:
            log.info("Pausing")
            self.player.pause()
            self.paused = True
        elif not is_paused and self.paused:
            log.info("Resuming")
            self.player.resume()
            self.paused = False
            if starttime and server_now:
                elapsed = _elapsed_seconds(starttime, server_now)
                self.player.seek_to(elapsed)

    def _handle_player_position(self, data):
        """Process a player_position event for drift correction."""
        src = data.get("src", "")
        if src != "spotify" or self.current_track_uri is None:
            return

        server_pos = data.get("pos", 0)
        local_pos = self.player.get_position()
        if local_pos is None:
            return

        drift = abs(local_pos - server_pos)
        if drift > self.drift_threshold:
            log.info("Drift correction: local=%.1fs server=%ds (drift=%.1fs)",
                     local_pos, server_pos, drift)
            self.player.seek_to(server_pos)

    def run(self):
        """Main loop: connect to SSE, process events, reconnect on failure."""
        backoff = 5
        max_backoff = 60

        while True:
            try:
                log.info("Connecting to %s/api/events ...", self.server)
                resp = requests.get(
                    f"{self.server}/api/events",
                    headers=self._headers(),
                    stream=True,
                    timeout=(10, None),  # 10s connect, no read timeout
                )
                resp.raise_for_status()
                log.info("Connected — listening for events")
                backoff = 5  # Reset on successful connect

                # Sync current state before waiting for events
                self._initial_sync()

                client = sseclient.SSEClient(resp)
                for event in client.events():
                    try:
                        data = json.loads(event.data)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if event.event == "now_playing":
                        self._handle_now_playing(data)
                    elif event.event == "player_position":
                        self._handle_player_position(data)
                    # queue_update and volume events are ignored

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 401:
                    log.error("Authentication failed (401) — check your token")
                    return  # Don't retry auth failures
                log.warning("HTTP error: %s", e)
            except requests.exceptions.ConnectionError as e:
                log.warning("Connection error: %s", e)
            except Exception as e:
                log.warning("Unexpected error: %s", e)

            log.info("Reconnecting in %ds ...", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
