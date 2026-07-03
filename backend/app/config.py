from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# In Docker, env vars are injected directly by docker-compose's `env_file:` and this
# path won't exist — that's fine, pydantic-settings falls back to os.environ.
# Locally, .env lives at the repo root (one level above backend/), not in this
# package, so we point at it explicitly rather than relying on cwd.
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
