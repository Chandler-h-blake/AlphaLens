from app.core.config import get_settings
from app.repositories.factory import get_research_repository
from app.repositories.research_repository import ResearchRepository, ResearchReportRecord
from app.schemas.research import (
    ResearchReportDetail,
    ResearchReportListItem,
    ResearchReportListResponse,
    SourceReference,
)


DISCLAIMER = "仅供研究学习，不构成投资建议。"


class ResearchService:
    def __init__(self, repository: ResearchRepository | None = None) -> None:
        settings = get_settings()
        self.repository = repository or get_research_repository(settings)

    def list_reports(self) -> ResearchReportListResponse:
        reports = self.repository.list_reports()
        return ResearchReportListResponse(
            source="AlphaLens 研究报告库",
            items=[self._to_list_item(report) for report in reports],
            total=len(reports),
        )

    def get_report(self, symbol: str) -> ResearchReportDetail:
        report = self.repository.get_report(symbol)
        sources = (
            [SourceReference.model_validate(source) for source in report.sources]
            if report.sources
            else [
                SourceReference(name="AlphaLens 多因子评分快照", type="internal_data"),
                SourceReference(name=report.source_file, type="seed_markdown_report"),
            ]
        )
        return ResearchReportDetail(
            **self._to_list_item(report).model_dump(),
            content_markdown=report.content_markdown,
            sources=sources,
            disclaimer=DISCLAIMER,
        )

    @staticmethod
    def _to_list_item(report: ResearchReportRecord) -> ResearchReportListItem:
        return ResearchReportListItem(
            symbol=report.symbol,
            name=report.name,
            title=report.title,
            industry=report.industry,
            generated_at=report.generated_at,
        )
