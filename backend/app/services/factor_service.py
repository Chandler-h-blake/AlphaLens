from math import isnan

import pandas as pd

from app.core.config import get_settings
from app.repositories.factory import get_factor_repository
from app.repositories.factor_repository import FactorRepository
from app.schemas.factors import (
    FactorOverviewItem,
    FactorOverviewResponse,
    FactorTopPoolItem,
    FactorTopPoolResponse,
)


CORE_COLUMNS = {"rank", "symbol", "name", "industry", "composite_score"}


def _optional_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return None if isnan(number) else number


class FactorService:
    """Convert factor snapshots into stable API responses."""

    def __init__(self, repository: FactorRepository | None = None) -> None:
        settings = get_settings()
        self.repository = repository or get_factor_repository(settings)

    def get_top_pool(
        self,
        *,
        keyword: str | None,
        industry: str | None,
        limit: int,
    ) -> FactorTopPoolResponse:
        frame = self.repository.get_top_pool()
        filtered = self._filter_top_pool(frame, keyword=keyword, industry=industry)
        records = filtered.sort_values(["rank", "symbol"]).head(limit).to_dict("records")
        items = [self._to_top_pool_item(record) for record in records]
        return FactorTopPoolResponse(
            source="AlphaLens 因子评分快照",
            items=items,
            total=len(filtered),
        )

    def get_overview(self) -> FactorOverviewResponse:
        frame = self.repository.get_overview().sort_values(["weight", "factor"], ascending=[False, True])
        records = frame.to_dict("records")
        return FactorOverviewResponse(
            source="AlphaLens 因子验证快照",
            items=[self._to_overview_item(record) for record in records],
            total=len(records),
        )

    @staticmethod
    def _filter_top_pool(
        frame: pd.DataFrame,
        *,
        keyword: str | None,
        industry: str | None,
    ) -> pd.DataFrame:
        result = frame.copy()
        if keyword:
            normalized_keyword = keyword.strip().casefold()
            symbol_match = result["symbol"].astype(str).str.casefold().str.contains(normalized_keyword, na=False)
            name_match = result["name"].astype(str).str.casefold().str.contains(normalized_keyword, na=False)
            result = result[symbol_match | name_match]
        if industry:
            normalized_industry = industry.strip().casefold()
            result = result[result["industry"].astype(str).str.casefold() == normalized_industry]
        return result

    @staticmethod
    def _to_top_pool_item(record: dict[str, object]) -> FactorTopPoolItem:
        factor_values = {
            key: _optional_number(value)
            for key, value in record.items()
            if key not in CORE_COLUMNS
        }
        return FactorTopPoolItem(
            symbol=str(record["symbol"]).zfill(6),
            name=str(record["name"]),
            industry=str(record["industry"]),
            rank=int(record["rank"]),
            composite_score=float(record["composite_score"]),
            factor_values=factor_values,
        )

    @staticmethod
    def _to_overview_item(record: dict[str, object]) -> FactorOverviewItem:
        optional_fields = {
            "spearman_ic_adjusted",
            "pearson_ic_adjusted",
            "ic_positive_rate",
            "group1_minus_group5",
            "group_spread_positive_rate",
            "validation_n",
        }
        data = {
            key: (_optional_number(value) if key in optional_fields else value)
            for key, value in record.items()
        }
        if pd.isna(data.get("snapshot_count")):
            data["snapshot_count"] = None
        elif data.get("snapshot_count") is not None:
            data["snapshot_count"] = int(data["snapshot_count"])
        data["direction"] = int(data["direction"])
        data["weight"] = float(data["weight"])
        return FactorOverviewItem.model_validate(data)
