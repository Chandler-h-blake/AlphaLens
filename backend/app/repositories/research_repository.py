from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import re

from app.core.exceptions import DataSourceError, ResourceNotFoundError


REPORT_FILENAME_PATTERN = re.compile(r"^(?P<symbol>\d{6})_(?P<name>.+)_report\.md$")
TITLE_PATTERN = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)
GENERATED_AT_PATTERN = re.compile(r"生成时间：(?P<value>[^\n]+)")
INDUSTRY_PATTERN = re.compile(r"^-\s*行业：(?P<value>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ResearchReportRecord:
    symbol: str
    name: str
    title: str
    industry: str | None
    generated_at: datetime | None
    content_markdown: str
    source_file: str
    sources: list[dict[str, str | None]] | None = None


class ResearchRepository:
    """Read bundled Markdown reports without changing the source files."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def list_reports(self) -> list[ResearchReportRecord]:
        if not self.reports_dir.exists():
            raise DataSourceError(f"未找到研究报告目录：{self.reports_dir}")
        reports = [self._parse_file(path) for path in self.reports_dir.glob("*_report.md")]
        return sorted(reports, key=lambda item: item.generated_at or datetime.min, reverse=True)

    def get_report(self, symbol: str) -> ResearchReportRecord:
        for report in self.list_reports():
            if report.symbol == symbol:
                return report
        raise ResourceNotFoundError(f"未找到股票代码 {symbol} 的研究报告。")

    def _parse_file(self, path: Path) -> ResearchReportRecord:
        match = REPORT_FILENAME_PATTERN.match(path.name)
        if not match:
            raise DataSourceError(f"研究报告文件名不符合约定：{path.name}")
        try:
            content = _read_markdown_cached(path, path.stat().st_mtime_ns)
        except (OSError, UnicodeDecodeError) as error:
            raise DataSourceError(f"无法读取研究报告 {path.name}：{error}") from error

        title = TITLE_PATTERN.search(content)
        generated_at = GENERATED_AT_PATTERN.search(content)
        industry = INDUSTRY_PATTERN.search(content)
        return ResearchReportRecord(
            symbol=match.group("symbol"),
            name=match.group("name"),
            title=title.group("title") if title else f"{match.group('name')}研究报告",
            industry=industry.group("value").strip() if industry else None,
            generated_at=_parse_datetime(generated_at.group("value")) if generated_at else None,
            content_markdown=content,
            source_file=path.name,
        )


@lru_cache(maxsize=32)
def _read_markdown_cached(path: Path, _: int) -> str:
    return path.read_text(encoding="utf-8")


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
