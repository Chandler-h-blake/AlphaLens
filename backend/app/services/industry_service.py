import pandas as pd

from app.core.config import get_settings
from app.repositories.factory import get_industry_repository
from app.repositories.industry_repository import IndustryRepository
from app.schemas.industry import IndustryDatesResponse, IndustryRotationItem, IndustryRotationResponse


def _optional_float(value: object) -> float | None:
    return None if pd.isna(value) else float(value)


class IndustryService:
    def __init__(self, repository: IndustryRepository | None = None) -> None:
        settings = get_settings()
        self.repository = repository or get_industry_repository(settings)

    def get_rotation(self) -> IndustryRotationResponse:
        frame = self.repository.get_rotation().sort_values(["rank_1m", "industry_name"])
        records = frame.to_dict("records")
        data_date = str(frame["last_date"].iloc[0]) if not frame.empty else ""
        return IndustryRotationResponse(
            source="AlphaLens 行业轮动快照",
            data_date=data_date,
            items=[self._to_item(record) for record in records],
            total=len(records),
        )

    def get_dates(self) -> IndustryDatesResponse:
        dates = self.repository.get_rotation()["last_date"].dropna().astype(str).unique().tolist()
        return IndustryDatesResponse(items=sorted(dates, reverse=True))

    @staticmethod
    def _to_item(record: dict[str, object]) -> IndustryRotationItem:
        return IndustryRotationItem(
            industry_code=str(record["industry_code"]),
            industry_name=str(record["industry_name"]),
            last_date=str(record["last_date"]),
            latest_close=_optional_float(record.get("latest_close")),
            return_1m=float(record["return_1m"]),
            return_3m=float(record["return_3m"]),
            rank_1m=int(record["rank_1m"]),
            rank_3m=int(record["rank_3m"]),
            rotation_type=str(record["rotation_type"]),
            generated_at=str(record["generated_at"]),
        )
