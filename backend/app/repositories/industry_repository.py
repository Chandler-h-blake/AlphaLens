from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.exceptions import DataSourceError


REQUIRED_COLUMNS = {
    "industry_code",
    "industry_name",
    "last_date",
    "return_1m",
    "return_3m",
    "rank_1m",
    "rank_3m",
    "rotation_type",
    "generated_at",
}


class IndustryRepository:
    """Read the bundled industry-rotation snapshot."""

    def __init__(self, rotation_file: Path) -> None:
        self.rotation_file = rotation_file

    def get_rotation(self) -> pd.DataFrame:
        try:
            frame = _read_rotation_cached(self.rotation_file, self.rotation_file.stat().st_mtime_ns)
        except FileNotFoundError as error:
            raise DataSourceError(f"未找到行业轮动数据文件：{self.rotation_file}") from error
        except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
            raise DataSourceError(f"无法读取行业轮动数据：{error}") from error
        missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
        if missing_columns:
            raise DataSourceError(f"行业轮动数据缺少字段：{'、'.join(sorted(missing_columns))}")
        return frame.copy()


@lru_cache(maxsize=8)
def _read_rotation_cached(path: Path, _: int) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype={"industry_code": str})
