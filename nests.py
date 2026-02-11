"""Nests helpers and manager.

This module provides helper functions for nest key generation, membership
tracking, and cleanup logic, plus the NestManager class for CRUD operations.
"""
import datetime
import json
import logging
import random
import string

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

def _nest_prefix(nest_id):
    """Return the Redis key prefix for a given nest."""
    return f"NEST:{nest_id}|"


# Legacy key mapping: maps old bare keys to their NEST:main| equivalents
# Used by migrate_keys.py and tests
legacy_key_mapping = {
    "MISC|now-playing": "NEST:main|MISC|now-playing",
    "MISC|priority-queue": "NEST:main|MISC|priority-queue",
    "MISC|current-done": "NEST:main|MISC|current-done",
    "MISC|started-on": "NEST:main|MISC|started-on",
    "MISC|paused": "NEST:main|MISC|paused",
    "MISC|force-jump": "NEST:main|MISC|force-jump",
    "MISC|master-player": "NEST:main|MISC|master-player",
    "MISC|player-now": "NEST:main|MISC|player-now",
    "MISC|playlist-plays": "NEST:main|MISC|playlist-plays",
    "MISC|last-queued": "NEST:main|MISC|last-queued",
    "MISC|last-bender-track": "NEST:main|MISC|last-bender-track",
    "MISC|bender_streak_start": "NEST:main|MISC|bender_streak_start",
    "MISC|now-playing-done": "NEST:main|MISC|now-playing-done",
    "MISC|last-played": "NEST:main|MISC|last-played",
    "MISC|volume": "NEST:main|MISC|volume",
    "MISC|update-pubsub": "NEST:main|MISC|update-pubsub",
    "MISC|backup-queue": "NEST:main|MISC|backup-queue",
    "MISC|backup-queue-data": "NEST:main|MISC|backup-queue-data",
    "MISC|guest-login": "NEST:main|MISC|guest-login",
    "MISC|guest-login-expire": "NEST:main|MISC|guest-login-expire",
    "AIRHORNS": "NEST:main|AIRHORNS",
}


def pubsub_channel(nest_id):
    """Return the pub/sub channel name for a given nest."""
    return f"NEST:{nest_id}|MISC|update-pubsub"


def members_key(nest_id):
    """Return the Redis key for the set of members in a nest."""
    return f"NEST:{nest_id}|MEMBERS"


def member_key(nest_id, email):
    """Return the Redis key for an individual member's heartbeat TTL."""
    return f"NEST:{nest_id}|MEMBER:{email}"


def refresh_member_ttl(redis_client, nest_id, email, ttl_seconds=90):
    """Set/refresh a member's heartbeat TTL key.

    Args:
        redis_client: Redis connection (caller provides, e.g. db._r)
        nest_id: The nest identifier
        email: Member's email address
        ttl_seconds: TTL in seconds (default 90)
    """
    key = member_key(nest_id, email)
    redis_client.setex(key, ttl_seconds, "1")


def should_delete_nest(metadata, members, queue_size, now):
    """Determine whether a nest should be cleaned up.

    Args:
        metadata: dict with keys 'is_main', 'last_activity' (ISO string),
                  'ttl_minutes' (int)
        members: int count of active members
        queue_size: int count of songs in queue
        now: datetime.datetime representing current time

    Returns:
        True if the nest should be deleted, False otherwise.
    """
    # Never delete the main nest
    if metadata.get("is_main"):
        return False

    # Don't delete if there are active members
    if members > 0:
        return False

    # Don't delete if there are songs in the queue
    if queue_size > 0:
        return False

    # Check inactivity timeout
    last_activity_str = metadata.get("last_activity")
    ttl_minutes = metadata.get("ttl_minutes", 120)

    if last_activity_str:
        last_activity = datetime.datetime.fromisoformat(last_activity_str)
        elapsed = (now - last_activity).total_seconds() / 60.0
        if elapsed >= ttl_minutes:
            return True

    return False


# ---------------------------------------------------------------------------
# Module-level join/leave wrappers (delegate to default NestManager in T6)
# ---------------------------------------------------------------------------

def join_nest(nest_id, email):
    """Add a member to a nest. Delegates to default NestManager."""
    raise NotImplementedError


def leave_nest(nest_id, email):
    """Remove a member from a nest. Delegates to default NestManager."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# NestManager class (stub until T6)
# ---------------------------------------------------------------------------

class NestManager:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def create_nest(self, creator_email, name=None):
        raise NotImplementedError

    def get_nest(self, nest_id):
        raise NotImplementedError

    def list_nests(self):
        raise NotImplementedError

    def delete_nest(self, nest_id):
        raise NotImplementedError

    def touch_nest(self, nest_id):
        raise NotImplementedError

    def join_nest(self, nest_id, email):
        raise NotImplementedError

    def leave_nest(self, nest_id, email):
        raise NotImplementedError

    def generate_code(self):
        raise NotImplementedError
