"""Refresh persisted public-market snapshots for the highest-ranked research stocks."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.factor_service import FactorService  # noqa: E402
from app.services.market_data_service import MarketDataService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=30, help="Number of stocks to refresh from the ranked pool.")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Pause between providers to avoid burst traffic.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.delay_seconds < 0:
        raise SystemExit("--limit must be positive and --delay-seconds cannot be negative.")

    items = FactorService().get_top_pool(keyword=None, industry=None, limit=args.limit).items
    market_service = MarketDataService()
    failures: list[str] = []
    for index, item in enumerate(items):
        try:
            result = market_service.refresh_stock(item.symbol)
            print(f"{item.symbol} {item.name}: {result.freshness}")
        except Exception as error:  # One provider failure should not stop the whole watchlist.
            failures.append(item.symbol)
            print(f"{item.symbol} {item.name}: failed ({error})", file=sys.stderr)
        if index < len(items) - 1:
            time.sleep(args.delay_seconds)

    print(f"Refresh complete: {len(items) - len(failures)}/{len(items)} succeeded.")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
