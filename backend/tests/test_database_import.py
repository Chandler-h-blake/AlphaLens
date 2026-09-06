from pathlib import Path
import subprocess
import sys

from sqlalchemy import select

from app.db.models import FactorScore, IndustryRotation, ResearchReport
from app.db.session import get_session_factory
from app.repositories.database_repository import DatabaseRepository


def test_seed_import_populates_sqlite_database(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'research.db'}"
    script = Path(__file__).resolve().parents[2] / "scripts" / "import_seed_data.py"
    result = subprocess.run([sys.executable, str(script), "--database-url", database_url], check=False, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    session_factory = get_session_factory(database_url)
    with session_factory() as session:
        assert len(session.scalars(select(FactorScore)).all()) == 30
        assert len(session.scalars(select(ResearchReport)).all()) == 5
        assert len(session.scalars(select(IndustryRotation)).all()) == 31

    repository = DatabaseRepository(database_url)
    assert len(repository.get_top_pool()) == 30
    assert len(repository.get_overview()) == 9
    assert len(repository.list_reports()) == 5
    assert len(repository.get_rotation()) == 31

    repeated = subprocess.run([sys.executable, str(script), "--database-url", database_url], check=False, capture_output=True, text=True)
    assert repeated.returncode == 0, repeated.stderr
    assert "跳过初始化" in repeated.stdout
