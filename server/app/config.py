import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        app_env = os.getenv("APP_ENV", "prod").strip().lower()

        explicit_database_url = os.getenv("DATABASE_URL")
        if app_env == "dev" and not explicit_database_url:
            db_dir = Path(__file__).resolve().parent.parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = (db_dir / "andromeda-dev.db").resolve()
            self.database_url = f"sqlite:///{db_path.as_posix()}"
        else:
            self.database_url = explicit_database_url or os.environ["DATABASE_URL"]

        self.session_secret: str = os.getenv("SESSION_SECRET", "dev-session-secret")
        self.private_key_b64: str | None = os.getenv("PRIVATE_KEY_B64")
        self.private_key_pem: str | None = os.getenv("PRIVATE_KEY_PEM")
        self.admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password: str = os.getenv("ADMIN_PASSWORD", "admin")
        self.app_env = app_env


settings = Settings()
