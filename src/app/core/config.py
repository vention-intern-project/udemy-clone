import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "udemy_clone")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    SECRET_KEY = os.getenv("SECRET_KEY", "udemy_ADT!123")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "1"))

    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")
    MAIL_PORT = os.getenv("MAIL_PORT", "587")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "")
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "")
    MEDIA_ROOT = os.getenv("MEDIA_ROOT", "media")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-31b-it:free")

    @property
    def DATABASE_URL(self):
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )


settings = Settings()
