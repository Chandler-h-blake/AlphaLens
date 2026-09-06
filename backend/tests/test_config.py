from app.core.config import Settings, normalize_database_url


def test_standard_postgres_urls_select_the_installed_psycopg_driver() -> None:
    raw_url = "postgresql://user:password@database.internal:5432/ai_research"

    assert normalize_database_url(raw_url) == "postgresql+psycopg://user:password@database.internal:5432/ai_research"
    assert Settings(database_url=raw_url).database_url == "postgresql+psycopg://user:password@database.internal:5432/ai_research"
