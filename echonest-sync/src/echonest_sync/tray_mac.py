"""macOS tray app using rumps."""

import json
import logging
import os
import time
import webbrowser

import rumps

from .autostart import disable_autostart, enable_autostart, is_autostart_enabled
from .updater import check_for_update, CURRENT_VERSION

log = logging.getLogger(__name__)


def _resource_path(name):
    """Resolve resource path — works in dev, pip install, and PyInstaller."""
    import sys
    candidates = []
    # PyInstaller bundle: resources are at _MEIPASS/resources/
    if getattr(sys, '_MEIPASS', None):
        candidates.append(os.path.join(sys._MEIPASS, "resources"))
    # Dev layout: echonest-sync/resources/
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))), "..", "resources"))
    # Pip install layout
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
    for d in candidates:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return name  # Fallback


class EchoNestSync(rumps.App):
    def __init__(self, channel, server=None, token=None, email=None, player=None):
        super().__init__("EchoNest", icon=_resource_path("icon_grey.png"),
                         template=False, quit_button=None)
        self.channel = channel
        self._server = server
        self._token = token
        self._linked_email = email
        self._player = player  # local Spotify player for mini player controls

        # State
        self._sync_paused = False
        self._player_paused = False  # Server playback paused
        self._connected = False
        self._last_disconnect = 0
        self._current_track = "No track"
        self._airhorn_enabled = True

        # Mini player subprocess
        self._miniplayer_proc = None
        self._miniplayer_state = {}  # buffered track/paused state for init

        # Menu items
        self.status_item = rumps.MenuItem("Disconnected", callback=None)
        self.track_item = rumps.MenuItem("No track", callback=self.focus_spotify)
        self.queue_item = rumps.MenuItem("Up Next")
        self.queue_item.add(rumps.MenuItem("No upcoming tracks", callback=None))
        self.airhorn_item = rumps.MenuItem("Airhorns: On", callback=self.toggle_airhorn)
        if self._linked_email:
            self.search_item = rumps.MenuItem("Search & Add Song", callback=self.open_search)
            self.link_item = rumps.MenuItem(f"Linked: {self._linked_email}", callback=None)
        else:
            self.search_item = rumps.MenuItem("Search & Add Song (link account first)", callback=None)
            self.link_item = rumps.MenuItem("Link Account", callback=self.open_link)
        self.pause_item = rumps.MenuItem("Pause Sync", callback=self.toggle_pause)
        self.miniplayer_item = rumps.MenuItem("Mini Player", callback=self.toggle_miniplayer)
        self.open_item = rumps.MenuItem("Open EchoNest", callback=self.open_echonest)
        self.update_item = rumps.MenuItem("Check for Updates", callback=self.check_updates)
        self.autostart_item = rumps.MenuItem("Start at Login",
                                             callback=self.toggle_autostart)
        self.quit_item = rumps.MenuItem("Quit EchoNest Sync", callback=self.quit_app)

        self.menu = [
            self.status_item,
            self.track_item,
            self.queue_item,
            self.open_item,
            None,  # separator
            self.pause_item,
            self.miniplayer_item,
            self.airhorn_item,
            self.search_item,
            None,
            self.link_item,
            self.update_item,
            self.autostart_item,
            None,
            self.quit_item,
        ]

        # Set initial autostart checkmark
        self.autostart_item.state = is_autostart_enabled()

    @rumps.timer(1)
    def poll_events(self, _):
        """Poll IPC events from the sync engine."""
        for event in self.channel.get_events():
            self._handle_event(event)
        self._mp_poll()

    def _handle_event(self, event):
        etype = event.type
        kw = event.kwargs

        if etype == "connected":
            was_connected = self._connected
            self._connected = True
            self._update_icon("green")
            self._refresh_status()
            self._miniplayer_state["status"] = "connected"
            self._mp_send({"type": "status", "status": "connected"})
            if was_connected:
                rumps.notification("EchoNest Sync", "", "Reconnected",
                                   sound=False)
            else:
                rumps.notification("EchoNest Sync", "", "Connected to EchoNest",
                                   sound=False)

        elif etype == "disconnected":
            self._connected = False
            self._last_disconnect = time.time()
            self._update_icon("yellow")
            self._refresh_status()
            self._miniplayer_state["status"] = "disconnected"
            self._mp_send({"type": "status", "status": "disconnected"})
            reason = kw.get("reason", "")
            if reason == "auth_failed":
                rumps.notification("EchoNest Sync", "",
                                   "Authentication failed", sound=False)

        elif etype == "track_changed":
            title = kw.get("title", "")
            artist = kw.get("artist", "")
            if title and artist:
                self._current_track = f"{title} - {artist}"
            elif title:
                self._current_track = title
            else:
                self._current_track = kw.get("uri", "Unknown")
            self.track_item.title = f"♪ {self._current_track}"
            self._refresh_status()
            # Buffer + forward to mini player
            self._miniplayer_state["track"] = {
                "type": "track", "title": title, "artist": artist,
                "big_img": kw.get("big_img", ""),
                "duration": kw.get("duration", 0),
                "paused": self._player_paused,
            }
            self._mp_send(self._miniplayer_state["track"])

        elif etype == "status_changed":
            status = kw.get("status", "")
            if status == "paused":
                self._sync_paused = True
                self.pause_item.title = "Resume Sync"
                self._update_icon("yellow")
                self._refresh_airhorn_item()
            elif status == "syncing":
                self._sync_paused = False
                self.pause_item.title = "Pause Sync"
                self._update_icon("green")
                self._refresh_airhorn_item()
            elif status == "override":
                self._sync_paused = True
                self.pause_item.title = "Resume Sync"
                self._update_icon("yellow")
                self._refresh_airhorn_item()
                rumps.notification("EchoNest Sync", "",
                                   "You took over — click to rejoin",
                                   sound=False)
            elif status == "waiting":
                self._update_icon("grey")
            self._refresh_status()
            self._miniplayer_state["status"] = status
            self._mp_send({"type": "status", "status": status})

        elif etype == "player_paused":
            self._player_paused = kw.get("paused", False)
            self._refresh_status()
            self._miniplayer_state["paused"] = self._player_paused
            self._mp_send({"type": "paused", "paused": self._player_paused})

        elif etype == "player_position":
            self._mp_send({"type": "position", "pos": kw.get("pos", 0)})

        elif etype == "queue_updated":
            tracks = kw.get("tracks", [])
            self._update_queue(tracks)
            self._miniplayer_state["queue"] = tracks
            self._mp_send({"type": "queue", "tracks": tracks})

        elif etype == "user_override":
            pass  # Handled via status_changed

        elif etype == "airhorn_toggled":
            self._airhorn_enabled = kw.get("enabled", True)
            self._refresh_airhorn_item()
            self._miniplayer_state["airhorn"] = self._airhorn_enabled
            self._mp_send({"type": "airhorn", "enabled": self._airhorn_enabled})

        elif etype == "airhorn":
            pass  # Sound played by sync engine

        elif etype == "account_linked":
            email = kw.get("email", "")
            user_token = kw.get("user_token", "")
            if email:
                self._linked_email = email
                self.link_item.title = f"Linked: {email}"
                self.link_item.set_callback(None)
                self.search_item.title = "Search & Add Song"
                self.search_item.set_callback(self.open_search)
            if user_token:
                self._token = user_token

    def _refresh_status(self):
        """Update the status line to reflect connection + playback state."""
        if not self._connected:
            self.status_item.title = "Disconnected"
            return
        if self._sync_paused:
            self.status_item.title = "Connected - Sync Paused"
        elif self._player_paused:
            self.status_item.title = "Connected - Paused"
        elif self._current_track and self._current_track != "No track":
            self.status_item.title = "Connected - Now Playing"
        else:
            self.status_item.title = "Connected"

    def _refresh_airhorn_item(self):
        """Update airhorn menu text and interactivity based on sync pause state."""
        if self._sync_paused:
            self.airhorn_item.title = "Airhorns: Off (sync paused)"
            self.airhorn_item.set_callback(None)  # Grey out
        else:
            self.airhorn_item.title = f"Airhorns: {'On' if self._airhorn_enabled else 'Off'}"
            self.airhorn_item.set_callback(self.toggle_airhorn)  # Re-enable

    def _update_queue(self, tracks):
        """Replace the Up Next submenu items with current queue tracks."""
        self.queue_item.clear()
        if not tracks:
            self.queue_item.add(rumps.MenuItem("No upcoming tracks", callback=None))
        else:
            for i, track in enumerate(tracks[:15]):
                self.queue_item.add(rumps.MenuItem(f"{i + 1}. {track}", callback=None))
            if len(tracks) > 15:
                self.queue_item.add(rumps.MenuItem(
                    f"  + {len(tracks) - 15} more...", callback=None))

    def _update_icon(self, color):
        try:
            self.icon = _resource_path(f"icon_{color}.png")
        except Exception:
            pass

    def focus_spotify(self, _):
        import subprocess
        subprocess.Popen(["open", "-a", "Spotify"])

    def open_echonest(self, _):
        webbrowser.open("https://echone.st")

    def toggle_pause(self, _):
        if self._sync_paused:
            self.channel.send_command("resume")
        else:
            self.channel.send_command("pause")

    def _alert(self, title, message, ok="OK", cancel=None):
        """Show an alert dialog with the EchoNest icon."""
        from AppKit import NSAlert, NSImage, NSAlertFirstButtonReturn
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_(ok)
        if cancel:
            alert.addButtonWithTitle_(cancel)
        icon_path = _resource_path("icon_app.png")
        ns_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
        if ns_image:
            ns_image.setSize_((128, 128))
            alert.setIcon_(ns_image)
        return alert.runModal() == NSAlertFirstButtonReturn

    def check_updates(self, _):
        result = check_for_update()
        if result["available"]:
            v = result["version"]
            self.update_item.title = f"Update available: v{v}"
            if self._alert("Update Available",
                           f"Version {v} is ready to download.",
                           ok="Download", cancel="Later"):
                webbrowser.open(result["download_url"])
        else:
            self.update_item.title = f"Up to date (v{CURRENT_VERSION})"
            self._alert("No Updates",
                        f"You're on the latest version (v{CURRENT_VERSION}).")

    def toggle_airhorn(self, _):
        self._airhorn_enabled = not self._airhorn_enabled
        self._refresh_airhorn_item()
        self.channel.send_command("toggle_airhorn")

    def open_search(self, _):
        if self._server and self._token:
            from .search import launch_search
            launch_search(self._server, self._token)

    def open_link(self, _):
        if not (self._server and self._token):
            return
        # Open the linking page in the browser
        webbrowser.open(f"{self._server}/sync/link")
        # Show native NSAlert with text input for the code
        self._show_link_dialog()

    def _show_link_dialog(self):
        """Show a native macOS alert with a text field to enter the linking code."""
        from AppKit import NSAlert, NSImage, NSAlertFirstButtonReturn, NSTextField
        import requests as req

        alert = NSAlert.alloc().init()
        alert.setMessageText_("Link Account")
        alert.setInformativeText_("Enter the 6-character code from the browser:")
        alert.addButtonWithTitle_("Link")
        alert.addButtonWithTitle_("Cancel")

        icon_path = _resource_path("icon_app.png")
        ns_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
        if ns_image:
            ns_image.setSize_((128, 128))
            alert.setIcon_(ns_image)

        # Add text input field
        input_field = NSTextField.alloc().initWithFrame_(((0, 0), (200, 24)))
        input_field.setPlaceholderString_("e.g. A3K9X2")
        alert.setAccessoryView_(input_field)
        alert.window().setInitialFirstResponder_(input_field)

        result = alert.runModal()
        if result != NSAlertFirstButtonReturn:
            return

        code = str(input_field.stringValue()).strip()
        if not code:
            return

        # Exchange the code for a user token
        try:
            resp = req.post(
                f"{self._server}/api/sync-link",
                headers={"Authorization": f"Bearer {self._token}",
                         "Content-Type": "application/json"},
                json={"code": code},
                timeout=10,
            )
            if resp.status_code == 404:
                self._alert("Link Failed", "Invalid or expired code. Try again.")
                return
            if resp.status_code == 429:
                self._alert("Link Failed", "Too many attempts. Try again later.")
                return
            resp.raise_for_status()
            data = resp.json()

            email = data["email"]
            user_token = data["user_token"]

            # Persist the per-user token and email
            from .config import save_config, set_token
            set_token(user_token)
            save_config({"email": email})

            # Update tray state and live token
            self._linked_email = email
            self._token = user_token
            self.link_item.title = f"Linked: {email}"
            self.link_item.set_callback(None)

            self._alert("Linked!", f"Account linked as {email}\nRestart EchoNest Sync for full effect.")
        except Exception as e:
            log.error("Link failed: %s", e)
            self._alert("Link Failed", f"Error: {e}")

    def toggle_autostart(self, _):
        if is_autostart_enabled():
            disable_autostart()
            self.autostart_item.state = False
        else:
            enable_autostart()
            self.autostart_item.state = True

    # ------------------------------------------------------------------
    # Mini player subprocess
    # ------------------------------------------------------------------

    def toggle_miniplayer(self, _):
        if self._miniplayer_proc and self._miniplayer_proc.poll() is None:
            # Running — send quit
            self._mp_send({"type": "quit"})
            self._miniplayer_proc = None
            self.miniplayer_item.state = False
        else:
            self._spawn_miniplayer()

    def _spawn_miniplayer(self):
        import subprocess
        import sys

        _is_frozen = getattr(sys, "frozen", False)
        try:
            if _is_frozen:
                cmd = [sys.executable, "--miniplayer"]
            else:
                cmd = [sys.executable, "-m", "echonest_sync.miniplayer"]
            self._miniplayer_proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            )
            self.miniplayer_item.state = True
            log.info("Mini player spawned (pid=%d)", self._miniplayer_proc.pid)

            # Send buffered state so it initializes immediately
            status = self._miniplayer_state.get("status", "disconnected")
            self._mp_send({"type": "status", "status": status})
            track = self._miniplayer_state.get("track")
            if track:
                self._mp_send(track)
            if "paused" in self._miniplayer_state:
                self._mp_send({"type": "paused", "paused": self._miniplayer_state["paused"]})
            queue = self._miniplayer_state.get("queue", [])
            if queue:
                self._mp_send({"type": "queue", "tracks": queue})
            self._mp_send({"type": "airhorn", "enabled": self._miniplayer_state.get("airhorn", True)})
        except Exception as e:
            log.error("Failed to spawn mini player: %s", e)
            self._miniplayer_proc = None

    def _mp_send(self, msg):
        """Send a JSON message to the mini player subprocess stdin."""
        proc = self._miniplayer_proc
        if proc is None or proc.poll() is not None:
            return
        try:
            import json
            data = json.dumps(msg) + "\n"
            proc.stdin.write(data.encode())
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            log.debug("Mini player pipe broken")
            self._miniplayer_proc = None
            self.miniplayer_item.state = False

    def _mp_poll(self):
        """Check for messages from mini player stdout (non-blocking)."""
        import json as _json
        import select

        proc = self._miniplayer_proc
        if proc is None or proc.poll() is not None:
            if proc is not None and proc.poll() is not None:
                log.info("Mini player exited (code=%s)", proc.returncode)
                self._miniplayer_proc = None
                self.miniplayer_item.state = False
            return

        # Non-blocking read via select
        try:
            readable, _, _ = select.select([proc.stdout], [], [], 0)
        except (ValueError, OSError):
            return
        if not readable:
            return

        try:
            line = proc.stdout.readline()
            if not line:
                # EOF — child exited
                self._miniplayer_proc = None
                self.miniplayer_item.state = False
                return
            msg = _json.loads(line.decode().strip())
            if msg.get("type") == "closed":
                self._miniplayer_proc = None
                self.miniplayer_item.state = False
            elif msg.get("type") == "command":
                cmd = msg.get("cmd", "")
                if cmd == "toggle_airhorn":
                    self.channel.send_command("toggle_airhorn")
                elif cmd == "pause":
                    self.channel.send_command("pause")
                elif cmd == "resume":
                    self.channel.send_command("resume")
        except (json.JSONDecodeError, Exception) as e:
            log.debug("Mini player IPC error: %s", e)

    def quit_app(self, _):
        # Shut down mini player if running
        if self._miniplayer_proc and self._miniplayer_proc.poll() is None:
            self._mp_send({"type": "quit"})
            try:
                self._miniplayer_proc.wait(timeout=2)
            except Exception:
                self._miniplayer_proc.kill()
            self._miniplayer_proc = None
        self.channel.send_command("quit")
        rumps.quit_application()
