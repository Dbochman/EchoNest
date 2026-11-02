"""Offline checks for legacy executable source in public static assets."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StaticAssetHygieneTests(unittest.TestCase):
    def test_static_assets_do_not_include_php_source(self):
        php_files = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "static").rglob("*")
            if path.is_file() and path.suffix.lower() == ".php"
        ]
        self.assertEqual(php_files, [])

    def test_docker_build_excludes_legacy_php_assets(self):
        rules = (ROOT / ".dockerignore").read_text().splitlines()
        self.assertIn("**/*.php", rules)

    def test_docker_build_excludes_runtime_environment_files(self):
        rules = (ROOT / ".dockerignore").read_text().splitlines()
        self.assertIn(".env", rules)
        self.assertIn(".env.*", rules)


if __name__ == "__main__":
    unittest.main()
