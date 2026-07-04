from app.config import Settings


def _settings(database_url: str) -> Settings:
    return Settings(database_url=database_url, jwt_secret_key="test")


def test_plain_postgresql_url_gets_asyncpg_driver() -> None:
    settings = _settings("postgresql://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"


def test_postgres_scheme_gets_asyncpg_driver() -> None:
    """Some providers (Heroku-style) use the postgres:// scheme."""
    settings = _settings("postgres://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"


def test_url_already_specifying_asyncpg_is_left_alone() -> None:
    settings = _settings("postgresql+asyncpg://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://user:pw@host:5432/db"
