"""Offline tests: do not load app config, stored credentials, or live services."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "tls_packaging", ROOT / "tools" / "check_tls_bundle.py"
)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class TLSPackagingTests(unittest.TestCase):
    def test_old_or_unrecognized_release_is_rejected_before_reading_bundle(self):
        for release in ("2026.10.18", "2025.1.1", "2026.10.19rc1", "unknown"):
            with self.subTest(release=release), patch.object(preflight.ssl, "SSLContext") as ctx:
                with self.assertRaises(ValueError):
                    preflight.check_bundle(release, "not-read.pem")
                ctx.assert_not_called()

    def test_known_excluded_roots_are_rejected_even_with_new_version(self):
        for name in preflight.EXCLUDED_ROOTS:
            with self.subTest(root=name), patch.object(preflight.ssl, "SSLContext") as ctx:
                ctx.return_value.get_ca_certs.return_value = [
                    {"subject": ((("commonName", name),),)}
                ]
                with self.assertRaises(ValueError):
                    preflight.check_bundle("2026.10.19", "stale.pem")

    def test_empty_bundle_is_rejected(self):
        with patch.object(preflight.ssl, "SSLContext") as ctx:
            ctx.return_value.get_ca_certs.return_value = []
            with self.assertRaises(ValueError):
                preflight.check_bundle("2026.10.19", "empty.pem")

    def test_current_bundle_uses_only_explicit_roots(self):
        with patch.object(preflight.ssl, "SSLContext") as ctx:
            ctx.return_value.get_ca_certs.return_value = [
                {"subject": ((("commonName", "emSign ECC Root CA - C3"),),)}
            ]
            self.assertEqual(preflight.check_bundle("2026.10.19", "current.pem"), 1)
            ctx.assert_called_once_with(preflight.ssl.PROTOCOL_TLS_CLIENT)
            ctx.return_value.load_verify_locations.assert_called_once_with(cafile="current.pem")

    def test_missing_or_invalid_bundle_failure_is_not_swallowed(self):
        with patch.object(preflight.ssl, "SSLContext") as ctx:
            ctx.return_value.load_verify_locations.side_effect = OSError("missing")
            with self.assertRaises(OSError):
                preflight.check_bundle("2026.10.19", "missing.pem")

    def test_both_builders_stop_before_pyinstaller_on_preflight_failure(self):
        for platform, filename in (("macos", "build_app.py"), ("windows", "build_exe.py")):
            with self.subTest(platform=platform):
                build_spec = importlib.util.spec_from_file_location(
                    "build_" + platform, ROOT / "build" / platform / filename
                )
                builder = importlib.util.module_from_spec(build_spec)
                build_spec.loader.exec_module(builder)
                with patch.object(builder.subprocess, "check_call", side_effect=RuntimeError("blocked")) as call:
                    with self.assertRaises(RuntimeError):
                        builder.build()
                    call.assert_called_once_with([
                        builder.sys.executable, str(ROOT / "tools" / "check_tls_bundle.py")
                    ])


if __name__ == "__main__":
    unittest.main()
