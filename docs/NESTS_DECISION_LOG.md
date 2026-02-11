# Nests Implementation — Decision Log

Decisions made during overnight implementation of the Nests MVP (Phases 1-3).
Each entry documents what was decided, why, and any alternatives considered.

---

## D001: Migration uses DUMP+RESTORE+DEL, not RENAME
**Date:** 2026-02-11 (pre-implementation review)
**Context:** T3 migration script originally planned to use `RENAME` for each key.
**Decision:** Use `DUMP`+`RESTORE`+`DEL` (copy-then-delete) instead.
**Rationale:** `RENAME` clobbers if the destination key already exists, making partial re-runs unsafe. `DUMP`+`RESTORE` lets us check for destination existence first and skip with a warning, making the migration idempotent and safe for partial rollouts.
**Alternatives:** `RENAMENX` (fails silently on collision — harder to debug), `COPY` (Redis 6.2+ only, may not be available).

---

## D002: GET /api/nests requires authentication
**Date:** 2026-02-11 (pre-implementation review)
**Context:** T7 originally had `/api/nests` in `SAFE_PARAM_PATHS` with auth TBD.
**Decision:** All nest API routes require authentication (session auth or API token). Do NOT add to `SAFE_PARAM_PATHS`.
**Rationale:** Adding to `SAFE_PARAM_PATHS` bypasses the `before_request` session gate, making the endpoint fully public. This would leak the list of active nests (names, codes, creator emails) to anonymous users. Authenticated users can list/access nests; API clients use `@require_api_token`.

---

## D003: Migration covers all 9 Redis key prefix families
**Date:** 2026-02-11 (pre-implementation review)
**Context:** T3 originally listed only `MISC|*`, `QUEUE|*`, `FILTER|*`, `BENDER|*` for migration.
**Decision:** Expand SCAN to cover all 9 prefix families found in db.py: `MISC|*`, `QUEUE|*`, `FILTER|*`, `BENDER|*`, `QUEUEJAM|*`, `COMMENTS|*`, `FILL-INFO|*`, `AIRHORNS`, `FREEHORN_*`.
**Rationale:** Missing prefixes would leave orphaned data under old key names, invisible to the nest-scoped DB class. Users would lose jams, comments, airhorn history, and fill-info cache.

---

## D004: Membership heartbeat TTL for stale member cleanup
**Date:** 2026-02-11 (pre-implementation review)
**Context:** T9 originally only did join/leave on WebSocket connect/disconnect without liveness tracking.
**Decision:** Add per-member TTL keys (`NEST:{id}|MEMBER:{email}` with 90s TTL) refreshed every 30s in the WebSocket serve loop.
**Rationale:** Without heartbeat, a browser crash or network drop leaves a stale entry in the MEMBERS set forever. Stale members prevent cleanup (cleanup checks member count > 0 → won't delete). The TTL keys naturally expire, and cleanup can check for expired member keys to detect truly empty nests.

---

## D005: Spotify rate limit key stays global
**Date:** 2026-02-11 (pre-implementation review)
**Context:** T2 wraps all DB class Redis keys with `_key()` for nest-scoping.
**Decision:** `MISC|spotify-rate-limited` must NOT be wrapped. It's a global Spotify API concern, not per-nest.
**Rationale:** Rate limiting is per-Spotify-app, not per-nest. If one nest triggers a rate limit, all nests should back off. The key is already used in module-level functions (not DB class methods), so it naturally stays global — but T2 should explicitly verify it wasn't accidentally wrapped.
