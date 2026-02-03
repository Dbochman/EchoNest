import os

os.environ.setdefault("SKIP_SPOTIFY_PREFETCH", "1")

from config import CONF  # noqa: E402
from app import app  # noqa: E402


def _get_client():
    app.testing = True
    return app.test_client()


def test_requires_login_when_no_dev_bypass():
    CONF.DEBUG = True
    CONF.DEV_AUTH_EMAIL = ""
    with _get_client() as client:
        resp = client.get("/", base_url="http://localhost:5000")
        assert resp.status_code == 302
        assert "/login/" in resp.location


def test_dev_bypass_sets_session():
    CONF.DEBUG = True
    CONF.DEV_AUTH_EMAIL = "dev@example.com"
    with _get_client() as client:
        resp = client.get("/", base_url="http://localhost:5000")
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess["email"] == "dev@example.com"
