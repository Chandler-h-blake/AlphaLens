from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.exceptions import DataSourceError


TOP_POOL_FILE = "final_top30_stock_pool.csv"
OVERVIEW_FILE = "final_factor_overview.csv"


class FactorRepository:
    """Read-only adapter for bundled factor seed snapshots."""

    def __init__(self, data_dir: Path, industry_mapping_file: Path | None = None) -> None:
        self.data_dir = data_dir
        self.industry_mapping_file = industry_mapping_file

    def get_top_pool(self) -> pd.DataFrame:
        frame = self._read_csv(TOP_POOL_FILE, required_columns={"rank", "symbol", "name", "industry", "composite_score"})
        return self._fill_industries(frame)

    def get_overview(self) -> pd.DataFrame:
        return self._read_csv(
            OVERVIEW_FILE,
            required_columns={"factor", "name", "category", "direction", "weight"},
        )

    def _read_csv(self, filename: str, required_columns: set[str]) -> pd.DataFrame:
        file_path = self.data_dir / filename
        try:
            frame = _read_csv_cached(file_path, file_path.stat().st_mtime_ns)
        except FileNotFoundError as error:
            raise DataSourceError(f"未找到数据文件：{file_path}") from error
        except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
            raise DataSourceError(f"无法读取数据文件 {file_path.name}：{error}") from error

        missing_columns = required_columns.difference(frame.columns)
        if missing_columns:
            names = "、".join(sorted(missing_columns))
            raise DataSourceError(f"数据文件 {file_path.name} 缺少字段：{names}")

        return frame.copy()

    def _fill_industries(self, frame: pd.DataFrame) -> pd.DataFrame:
        if self.industry_mapping_file is None or not self.industry_mapping_file.exists():
            return frame
        try:
            mapping = _read_csv_cached(self.industry_mapping_file, self.industry_mapping_file.stat().st_mtime_ns)
        except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
            raise DataSourceError(f"无法读取行业映射文件：{error}") from error
        if not {"symbol", "industry"}.issubset(mapping.columns):
            raise DataSourceError("行业映射文件缺少 symbol 或 industry 字段。")
        result = frame.copy()
        industry_by_symbol = mapping.set_index("symbol")["industry"]
        mapped_industry = result["symbol"].map(industry_by_symbol)
        missing = result["industry"].isna() | result["industry"].astype(str).isin({"", "unknown"})
        result.loc[missing, "industry"] = mapped_industry[missing].fillna("unknown")
        return result


@lru_cache(maxsize=8)
def _read_csv_cached(file_path: Path, _: int) -> pd.DataFrame:
    """Cache by file modification time so changed CSVs are refreshed automatically."""

    return pd.read_csv(file_path, dtype={"symbol": str}, encoding="utf-8-sig")
