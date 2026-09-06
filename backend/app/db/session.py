from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import normalize_database_url


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    return create_engine(normalize_database_url(database_url), pool_pre_ping=True)


def get_session_factory(database_url: str) -> sessionmaker:
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False)
