from app.core.config import Settings, get_settings
from app.core.exceptions import DataSourceError
from app.repositories.database_repository import DatabaseRepository
from app.repositories.factor_repository import FactorRepository
from app.repositories.industry_repository import IndustryRepository
from app.repositories.research_repository import ResearchRepository


def _database_repository(settings: Settings) -> DatabaseRepository:
    if not settings.database_url:
        raise DataSourceError("DATA_BACKEND=database 时必须配置 DATABASE_URL。")
    return DatabaseRepository(settings.database_url)


def get_factor_repository(settings: Settings | None = None):
    current = settings or get_settings()
    return _database_repository(current) if current.data_backend == "database" else FactorRepository(current.seed_factor_path, current.seed_industry_mapping_path)


def get_research_repository(settings: Settings | None = None):
    current = settings or get_settings()
    return _database_repository(current) if current.data_backend == "database" else ResearchRepository(current.seed_research_path)


def get_industry_repository(settings: Settings | None = None):
    current = settings or get_settings()
    return _database_repository(current) if current.data_backend == "database" else IndustryRepository(current.seed_industry_rotation_path)
