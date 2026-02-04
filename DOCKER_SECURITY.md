# Docker Security Hardening

This document details the security hardening measures implemented for Andre's Docker deployment.

## Overview

The Docker configuration has been hardened following [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) recommendations.

## Security Measures Implemented

### 1. Non-Root User (Critical)

**Risk**: Containers running as root can escape to host with elevated privileges.

**Implementation**:
- Created dedicated `andre` user (UID/GID 1000) in Dockerfile
- All containers run as non-root via `user: "1000:1000"` in docker-compose
- Application files owned by non-root user

```dockerfile
RUN groupadd --gid 1000 andre && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home andre
USER andre
```

### 2. Pinned Image Versions (High)

**Risk**: Unpinned images can introduce breaking changes or vulnerabilities.

**Implementation**:
- Python base image pinned with SHA256 digest
- Redis image pinned with SHA256 digest

```yaml
image: python:3.11-slim-bookworm@sha256:549988ff0804593d8373682ef5c0f0ceee48328abaaa2e054241c23f5c324751
image: redis:7-alpine@sha256:02f2cc4882f8bf87c79a220ac958f58c700bdec0dfb9b9ea61b62fb0e8f1bfcf
```

### 3. Custom Docker Networks (High)

**Risk**: Default bridge network allows unrestricted cross-container communication.

**Implementation**:
- `andre_network`: External network for Spotify/OAuth API access
- `andre_internal`: Internal-only network (no internet access)
- Redis isolated to internal network only
- App containers on both networks

```yaml
networks:
  andre_network:
    internal: false  # Internet access for APIs
  andre_internal:
    internal: true   # No internet access
```

### 4. Resource Limits (Medium)

**Risk**: Containers without limits can exhaust host resources (DoS).

**Implementation**:
| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| Redis   | 0.5       | 256M         |
| Andre   | 1.0       | 512M         |
| Player  | 0.5       | 256M         |

### 5. Read-Only Filesystem (Medium)

**Risk**: Writable filesystems allow malware persistence.

**Implementation**:
- All containers use `read_only: true`
- tmpfs mounts for `/tmp` and `__pycache__`
- Only necessary directories mounted writable (`play_logs`, `oauth_creds`)

### 6. Dropped Capabilities (Medium)

**Risk**: Default Linux capabilities allow privileged operations.

**Implementation**:
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

### 7. Health Checks (Low)

**Risk**: Unhealthy containers may continue serving traffic.

**Implementation**:
- Redis: `redis-cli ping`
- Andre: HTTP check on `/health` endpoint
- Configurable intervals, timeouts, and retries

## Verification Commands

After deployment, verify each security measure:

```bash
# 1. Verify non-root user
docker exec andre_app whoami
# Expected: andre (not root)

# 2. Verify read-only filesystem
docker exec andre_app touch /test
# Expected: Read-only file system error

# 3. Verify capabilities dropped
docker exec andre_app cat /proc/1/status | grep Cap
# Expected: CapEff should be minimal (0000000000000000)

# 4. Verify resource limits
docker stats --no-stream
# Expected: MEM LIMIT shows configured values

# 5. Verify network isolation
docker exec andre_redis ping -c 1 8.8.8.8
# Expected: Should fail (internal network only)

# 6. Verify health check
docker inspect andre_app --format='{{.State.Health.Status}}'
# Expected: healthy
```

## Files Modified

| File | Changes |
|------|---------|
| `Dockerfile` | Non-root user, curl for healthcheck, pinned base image |
| `docker-compose.yaml` | Networks, resource limits, read-only FS, security options, health checks |

## Rollback

If issues occur after deployment:

```bash
git checkout HEAD~1 -- docker-compose.yaml Dockerfile
docker compose down
docker compose up -d --build
```

## References

- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
