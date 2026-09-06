from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import select

from app.core.config import Settings
from app.core.exceptions import LLMConfigurationError
from app.db.base import Base
from app.db.models import ResearchTask, WorkspaceSnapshot
from app.db.session import get_engine, get_session_factory
from app.repositories.research_task_repository import DatabaseTaskStore
from app.services.dashboard_service import DashboardService
from app.services.review_service import ReviewService


def setup(tmp_path):
    url = f"sqlite:///{tmp_path / 'workspace.db'}"
    Base.metadata.create_all(get_engine(url))
    DashboardService.seed_if_missing(url, Path(__file__).resolve().parents[2] / 'data/seed')
    return Settings(_env_file=None, database_url=url, llm_provider='disabled')


def test_seed_is_labeled_and_idempotent(tmp_path):
    settings = setup(tmp_path)
    DashboardService.seed_if_missing(settings.database_url, Path(__file__).resolve().parents[2] / 'data/seed')
    service = DashboardService(settings)
    result = service.get('dashboard')
    assert '合成' in result.warning
    assert result.freshness == 'stale'
    with get_session_factory(settings.database_url)() as session:
        assert len(session.scalars(select(WorkspaceSnapshot)).all()) == 2


def test_refresh_failure_preserves_provenance(tmp_path):
    service = DashboardService(setup(tmp_path))
    before = service.get('dashboard')
    with patch('app.services.dashboard_service.PublicDashboardProvider.fetch', side_effect=RuntimeError('offline')):
        result = service.refresh('dashboard')
    assert result.data == before.data
    assert result.fetched_at == before.fetched_at
    assert result.source == before.source
    assert result.freshness == 'stale'


def test_missing_key_never_creates_task(tmp_path):
    settings = setup(tmp_path)
    with pytest.raises(LLMConfigurationError):
        ReviewService(settings).create(BackgroundTasks())
    with get_session_factory(settings.database_url)() as session:
        assert session.scalars(select(ResearchTask)).all() == []


def test_shared_task_recovery_includes_reviews(tmp_path):
    settings = setup(tmp_path)
    with get_session_factory(settings.database_url).begin() as session:
        session.add(ResearchTask(id='review-test', symbol='', kind='daily_review', status='running'))
    assert DatabaseTaskStore(settings.database_url).mark_interrupted_tasks() == 1
    with get_session_factory(settings.database_url)() as session:
        assert session.get(ResearchTask, 'review-test').status == 'failed'
