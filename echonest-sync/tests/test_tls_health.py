import ssl
import runpy
import sys
import unittest
from unittest.mock import patch

from echonest_sync import tls_health


class TLSHealthTests(unittest.TestCase):
    def test_self_test_entrypoint_does_not_import_app_or_keyring(self):
        with patch.object(sys, "argv", ["echonest-sync", "--tls-self-test"]), \
                patch.dict(sys.modules, {"echonest_sync.app": None, "keyring": None}), \
                patch.object(tls_health, "main", return_value=0):
            with self.assertRaises(SystemExit) as result:
                runpy.run_module("echonest_sync", run_name="__main__")
            self.assertEqual(result.exception.code, 0)

    def test_targets_cover_both_paths_and_controls(self):
        self.assertEqual(len(tls_health.CANARIES), 12)
        self.assertEqual(len(tls_health.CONTROLS), 2)

    def test_inconclusive_is_never_a_pass(self):
        for results in ([], [{"result": "inconclusive"}], [{"result": "canary_changed"}]):
            self.assertEqual(tls_health.exit_code(results), 2)
        self.assertEqual(tls_health.exit_code([{"result": "exposed"}]), 1)
        self.assertEqual(tls_health.exit_code([{"result": "rejected"}, {"result": "control_passed"}]), 0)

    def test_only_trust_errors_count_as_rejection(self):
        for code, expected in ((20, "rejected"), (23, "rejected"), (10, "inconclusive"), (62, "inconclusive")):
            error = ssl.SSLCertVerificationError("test")
            error.verify_code = code
            with self.subTest(code=code), patch.object(tls_health.socket, "create_connection", side_effect=error):
                self.assertEqual(tls_health.probe("test", "expected", None)["result"], expected)
                self.assertEqual(tls_health.probe("control", None, None)["result"], "inconclusive")

    def test_network_failure_is_inconclusive(self):
        with patch.object(tls_health.socket, "create_connection", side_effect=TimeoutError):
            self.assertEqual(tls_health.probe("test", "expected", None)["result"], "inconclusive")
