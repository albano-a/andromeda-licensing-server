import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class DevDatabaseConfigTests(unittest.TestCase):
    def _reload_config(self, env_overrides):
        base_env = {
            "SESSION_SECRET": "dev-secret",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password",
        }
        base_env.update(env_overrides)

        with patch.dict(os.environ, base_env, clear=True):
            for module_name in [
                "app.config",
                "app.database",
                "app.main",
                "app.models",
                "app.routers.admin_api",
                "app.routers.admin_ui",
                "app.routers.verify",
            ]:
                sys.modules.pop(module_name, None)

            import app.config as config

            importlib.reload(config)
            return config.settings

    def test_uses_sqlite_when_dev_mode_is_enabled_without_database_url(self):
        settings = self._reload_config({"APP_ENV": "dev"})

        self.assertTrue(settings.database_url.startswith("sqlite:///"))
        self.assertIn("andromeda-dev.db", settings.database_url)

    def test_keeps_explicit_database_url_when_provided(self):
        explicit_url = "postgresql+psycopg2://user:pass@localhost:5432/app"
        settings = self._reload_config({"DATABASE_URL": explicit_url, "APP_ENV": "dev"})

        self.assertEqual(settings.database_url, explicit_url)


if __name__ == "__main__":
    unittest.main()
