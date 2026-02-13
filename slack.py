"""Fire-and-forget Slack webhook notifications for EchoNest.

Posts deploy alerts, now-playing updates, and airhorn events to a Slack channel.
If SLACK_WEBHOOK_URL is not configured, all functions are silent no-ops.
"""

import json
import logging
import threading

import requests

from config import CONF

logger = logging.getLogger(__name__)


def _get_url():
    return getattr(CONF, 'SLACK_WEBHOOK_URL', None) or None


def post(text, blocks=None):
    """Fire-and-forget post to Slack. Never raises."""
    url = _get_url()
    if not url:
        return

    payload = {'text': text}
    if blocks:
        payload['blocks'] = blocks

    def _send():
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            logger.debug("slack.post failed", exc_info=True)

    threading.Thread(target=_send, daemon=True).start()


def notify_deploy():
    """Post deploy notification with resync reminder."""
    post("\U0001f504 EchoNest is restarting \u2014 you may need to resync audio.")


def _track_url(song):
    """Build a Spotify track URL from the song's trackid."""
    trackid = song.get('trackid', '')
    if trackid:
        track_id = trackid.split(':')[-1]
        return f"https://open.spotify.com/track/{track_id}"
    return ''


def _artist_url(song):
    """Extract the first artist's Spotify URL from the raw API data."""
    data = song.get('data', '')
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return ''
    if isinstance(data, dict):
        artists = data.get('artists', [])
        if artists:
            return artists[0].get('external_urls', {}).get('spotify', '')
    return ''


def notify_now_playing(song):
    """Post now-playing update with album art, title, artist, who added it."""
    if not song or not _get_url():
        return

    title = song.get('title', 'Unknown')
    artist = song.get('artist', 'Unknown')
    user = song.get('user', '')
    img = song.get('img', '')

    track_link = _track_url(song)
    artist_link = _artist_url(song)

    title_display = f"<{track_link}|{title}>" if track_link else f"*{title}*"
    artist_display = f"<{artist_link}|{artist}>" if artist_link else f"*{artist}*"

    text = f"\U0001f3b5 Now Playing: {title} by {artist}\nAdded by {user}"

    elements = [
        {
            'type': 'mrkdwn',
            'text': f"\U0001f3b5 Now Playing: *{title_display}* by *{artist_display}* \u2014 Added by {user}",
        },
    ]

    if img:
        elements.insert(0, {
            'type': 'image',
            'image_url': img,
            'alt_text': f"{title} album art",
        })

    blocks = [{'type': 'context', 'elements': elements}]

    post(text, blocks=blocks)


def notify_airhorn(user, airhorn_name, song_title, song_artist):
    """Post airhorn event."""
    if not _get_url():
        return

    text = (
        f"\U0001f4ef {user} blasted the *{airhorn_name}* airhorn!\n"
        f"\U0001f3b5 During: {song_title} \u2014 {song_artist}"
    )
    post(text)


def notify_pause(user):
    """Post when playback is paused."""
    post(f"\u23f8\ufe0f {user} paused playback.")


def notify_skip(user, song_title, song_artist):
    """Post when a song is skipped."""
    post(f"\u23ed\ufe0f {user} skipped *{song_title}* by *{song_artist}*")


def notify_unpause(user):
    """Post when playback is unpaused."""
    post(f"\u25b6\ufe0f {user} unpaused playback.")


def notify_nest_created(nest):
    """Post when a new nest is created."""
    if not nest or not _get_url():
        return

    name = nest.get('name', nest.get('code', '???'))
    creator = nest.get('creator', '')
    code = nest.get('code', '')

    text = f"\U0001fab9 New nest created: *{name}* (code: `{code}`) by {creator}"
    post(text)
