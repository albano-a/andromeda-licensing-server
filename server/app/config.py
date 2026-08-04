import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.environ["DATABASE_URL"]
    session_secret: str = os.environ["SESSION_SECRET"]
    private_key_b64: str | None = os.getenv("PRIVATE_KEY_B64")
    private_key_pem: str | None = os.getenv("PRIVATE_KEY_PEM")
    admin_username: str = os.environ["ADMIN_USERNAME"]
    admin_password: str = os.environ["ADMIN_PASSWORD"]


settings = Settings()
