import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.environ["DATABASE_URL"]
    session_secret: str = os.environ["SESSION_SECRET"]
    private_key_path: Path = Path(os.environ["PRIVATE_KEY_PATH"])
    admin_username: str = os.environ["ADMIN_USERNAME"]
    admin_password: str = os.environ["ADMIN_PASSWORD"]


settings = Settings()
