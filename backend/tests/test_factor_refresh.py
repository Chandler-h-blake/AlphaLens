from datetime import date, timedelta

import pandas as pd

from app.market.eastmoney_provider import DailyBar
from app.services.factor_refresh_service import FactorRefreshService


FACTORS = [
    "momentum_20d", "turnover_change", "pe_percentile", "pb_percentile", "roe",
    "gross_margin", "revenue_growth_yoy", "net_profit_growth_yoy", "volatility_60d",
]


def test_refresh_recomputes_technical_factors_and_ranks() -> None:
    start = date(2026, 1, 1)
    histories = {
        "000001": [DailyBar(start + timedelta(days=i), 10 + i * .1, 1 + i * .01) for i in range(70)],
        "000002": [DailyBar(start + timedelta(days=i), 20 - i * .05, 2 - i * .005) for i in range(70)],
    }
    source = pd.DataFrame([
        {"symbol": "000001", "name": "甲", "industry": "测试", **{factor: 1.0 for factor in FACTORS}},
        {"symbol": "000002", "name": "乙", "industry": "测试", **{factor: 2.0 for factor in FACTORS}},
    ])
    overview = pd.DataFrame({
        "factor": FACTORS,
        "weight": [0.2, 0.07, 0.04, 0.04, 0.15, 0.1, 0.22, 0.13, 0.05],
        "direction": [1, 1, -1, -1, 1, 1, 1, 1, -1],
    })

    result = FactorRefreshService._calculate(source, overview, histories, histories["000001"][-1].trading_date)

    assert list(result["rank"]) == [1, 2]
    by_symbol = result.set_index("symbol")
    assert by_symbol.loc["000001", "momentum_20d"] > by_symbol.loc["000002", "momentum_20d"]
    assert "volatility_60d_weighted_score" in result
