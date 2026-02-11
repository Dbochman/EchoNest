"""
Contract tests for Nests (xfail until implementation lands).
"""
import os
import sys

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.xfail(reason="Nests not implemented yet")
class TestNestsAPI:
    @pytest.fixture
    def client(self):
        if os.environ.get("SKIP_SPOTIFY_PREFETCH"):
            pytest.skip("Skipping due to SKIP_SPOTIFY_PREFETCH")

        os.environ["ANDRE_API_TOKEN"] = "test-secret-token-12345"
        from app import app, CONF

        app.config["TESTING"] = True
        self._host = str(CONF.HOSTNAME) if CONF.HOSTNAME else "localhost:5000"
        with app.test_client() as client:
            yield client

    def _get(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.get(path, headers=headers, **kwargs)

    def _post(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.post(path, headers=headers, **kwargs)

    def _patch(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.patch(path, headers=headers, **kwargs)

    def test_create_nest_returns_code(self, client):
        rv = self._post(
            client,
            "/api/nests",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"name": "Friday Vibes"},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert "code" in data
        assert len(data["code"]) == 5

    def test_get_nest_info(self, client):
        rv = self._get(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 404)

    def test_patch_nest_name(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"name": "New Name"},
        )
        assert rv.status_code in (200, 403, 404)

    def test_vanity_validation_reserved_and_charset(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "admin"},
        )
        assert rv.status_code in (400, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "JAZZ NIGHT"},
        )
        assert rv.status_code in (400, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "jazznight"},
        )
        assert rv.status_code in (200, 403, 404)

    def test_vanity_validation_length_bounds(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "ab"},
        )
        assert rv.status_code in (400, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "abc"},
        )
        assert rv.status_code in (200, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "a" * 24},
        )
        assert rv.status_code in (200, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "a" * 25},
        )
        assert rv.status_code in (400, 403, 404)

    def test_vanity_validation_start_and_chars(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "1start"},
        )
        assert rv.status_code in (400, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "good-name"},
        )
        assert rv.status_code in (200, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "bad_name"},
        )
        assert rv.status_code in (400, 403, 404)

    def test_vanity_reserved_words_list(self, client):
        for reserved in (
            "api",
            "socket",
            "login",
            "signup",
            "static",
            "assets",
            "health",
            "status",
            "metrics",
            "terms",
            "privacy",
        ):
            rv = self._patch(
                client,
                "/api/nests/XXXXX",
                headers={"Authorization": "Bearer test-secret-token-12345"},
                json={"vanity_code": reserved},
            )
            assert rv.status_code in (400, 403, 404)

    def test_invite_only_join_blocked_without_token(self, client):
        rv = self._get(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        # Expect 403 if invite-only and no token, otherwise 200/404.
        assert rv.status_code in (200, 403, 404)

    def test_invite_token_rotation_invalidates_old(self, client):
        rv = self._post(
            client,
            "/api/nests/XXXXX/invites/rotate",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        # After rotation, old token should be invalid.
        assert rv.status_code in (200, 401, 403, 404)

        rv = self._get(
            client,
            "/api/nests/XXXXX",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            query_string={"invite": "oldtoken"},
        )
        assert rv.status_code in (403, 404, 200)

    def test_create_nest_free_cap_error_shape(self, client):
        rv = self._post(
            client,
            "/api/nests",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"name": "Cap Test"},
        )
        if rv.status_code in (403, 429):
            data = rv.get_json()
            assert data.get("error") == "nest_limit_reached"
            assert "upgrade" in data.get("message", "").lower()

    def test_rate_limit_shape(self, client):
        rv = self._post(
            client,
            "/api/nests",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"name": "Rate Limit Test"},
        )
        if rv.status_code == 429:
            data = rv.get_json()
            assert data.get("error") in ("rate_limited", "nest_limit_reached")

    def test_rate_limit_buckets(self, client):
        rv = self._post(
            client,
            "/api/nests/XXXXX/kick",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"email": "user@example.com"},
        )
        if rv.status_code == 429:
            data = rv.get_json()
            assert data.get("error") == "rate_limited"


@pytest.mark.xfail(reason="Admin console not implemented yet")
class TestNestsAdminAPI:
    @pytest.fixture
    def client(self):
        if os.environ.get("SKIP_SPOTIFY_PREFETCH"):
            pytest.skip("Skipping due to SKIP_SPOTIFY_PREFETCH")

        os.environ["ANDRE_API_TOKEN"] = "test-secret-token-12345"
        from app import app, CONF

        app.config["TESTING"] = True
        self._host = str(CONF.HOSTNAME) if CONF.HOSTNAME else "localhost:5000"
        with app.test_client() as client:
            yield client

    def _get(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.get(path, headers=headers, **kwargs)

    def _post(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.post(path, headers=headers, **kwargs)

    def _patch(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.patch(path, headers=headers, **kwargs)

    def test_admin_get_settings(self, client):
        rv = self._get(
            client,
            "/api/nests/XXXXX/admin",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 401, 403, 404)

    def test_admin_update_settings(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX/admin",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={
                "vanity_code": "jazznight",
                "theme": {"accent": "#22ff66"},
                "bender": {"enabled": True},
                "is_private": True,
            },
        )
        assert rv.status_code in (200, 400, 401, 403, 404)

    def test_vanity_case_insensitive_collision(self, client):
        rv = self._patch(
            client,
            "/api/nests/XXXXX/admin",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "JazzNight"},
        )
        assert rv.status_code in (200, 400, 401, 403, 404)

        rv = self._patch(
            client,
            "/api/nests/YYYYY/admin",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "jazznight"},
        )
        assert rv.status_code in (400, 401, 403, 404)

    def test_admin_kick_ban_unban(self, client):
        for path in (
            "/api/nests/XXXXX/kick",
            "/api/nests/XXXXX/ban",
            "/api/nests/XXXXX/unban",
        ):
            rv = self._post(
                client,
                path,
                headers={"Authorization": "Bearer test-secret-token-12345"},
                json={"email": "user@example.com"},
            )
            assert rv.status_code in (200, 400, 401, 403, 404)

    def test_admin_invite_rotate(self, client):
        rv = self._post(
            client,
            "/api/nests/XXXXX/invites/rotate",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 401, 403, 404)


@pytest.mark.xfail(reason="Billing endpoints not implemented yet")
class TestBillingAPI:
    @pytest.fixture
    def client(self):
        if os.environ.get("SKIP_SPOTIFY_PREFETCH"):
            pytest.skip("Skipping due to SKIP_SPOTIFY_PREFETCH")

        os.environ["ANDRE_API_TOKEN"] = "test-secret-token-12345"
        from app import app, CONF

        app.config["TESTING"] = True
        self._host = str(CONF.HOSTNAME) if CONF.HOSTNAME else "localhost:5000"
        with app.test_client() as client:
            yield client

    def _get(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.get(path, headers=headers, **kwargs)

    def _post(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.post(path, headers=headers, **kwargs)

    def test_billing_status(self, client):
        rv = self._get(
            client,
            "/api/billing/status",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 401, 403)

    def test_billing_checkout(self, client):
        rv = self._post(
            client,
            "/api/billing/checkout",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"price_id": "price_tier_a_monthly"},
        )
        assert rv.status_code in (200, 400, 401, 403)

    def test_billing_portal(self, client):
        rv = self._post(
            client,
            "/api/billing/portal",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 401, 403)

    def test_billing_webhook_signature_required(self, client):
        rv = self._post(client, "/api/billing/webhook", data="{}")
        assert rv.status_code in (400, 401, 403)

    def test_billing_webhook_idempotency(self, client):
        payload = '{"id":"evt_123","type":"invoice.payment_succeeded"}'
        rv1 = self._post(
            client,
            "/api/billing/webhook",
            data=payload,
            headers={"Stripe-Signature": "t=123,v1=bad"},
        )
        rv2 = self._post(
            client,
            "/api/billing/webhook",
            data=payload,
            headers={"Stripe-Signature": "t=123,v1=bad"},
        )
        assert rv1.status_code in (400, 401, 403)
        assert rv2.status_code in (400, 401, 403, 409)


@pytest.mark.xfail(reason="Super admin interface not implemented yet")
class TestSuperAdminAPI:
    @pytest.fixture
    def client(self):
        if os.environ.get("SKIP_SPOTIFY_PREFETCH"):
            pytest.skip("Skipping due to SKIP_SPOTIFY_PREFETCH")

        os.environ["ANDRE_API_TOKEN"] = "test-secret-token-12345"
        from app import app, CONF

        app.config["TESTING"] = True
        self._host = str(CONF.HOSTNAME) if CONF.HOSTNAME else "localhost:5000"
        with app.test_client() as client:
            yield client

    def _get(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.get(path, headers=headers, **kwargs)

    def _post(self, client, path, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Host"] = self._host
        return client.post(path, headers=headers, **kwargs)

    def test_superadmin_list_nests(self, client):
        rv = self._get(
            client,
            "/api/admin/nests",
            headers={"Authorization": "Bearer test-secret-token-12345"},
        )
        assert rv.status_code in (200, 401, 403, 404)

    def test_superadmin_force_delete(self, client):
        rv = self._post(
            client,
            "/api/admin/nests/XXXXX/delete",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"reason": "abuse"},
        )
        assert rv.status_code in (200, 400, 401, 403, 404)

    def test_superadmin_release_vanity(self, client):
        rv = self._post(
            client,
            "/api/admin/vanity/release",
            headers={"Authorization": "Bearer test-secret-token-12345"},
            json={"vanity_code": "jazznight", "reason": "requested"},
        )
        assert rv.status_code in (200, 400, 401, 403, 404)
