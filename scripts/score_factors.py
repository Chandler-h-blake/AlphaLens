"""Recompute nine-factor ranks from a dated raw CSV and persist the TOP30.

Usage: PYTHONPATH=backend python scripts/score_factors.py --input raw.csv --data-date YYYY-MM-DD
Input columns match data/seed/factors/final_factor_scores.csv; existing score columns are ignored.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import select, delete
from app.core.config import get_settings
from app.db.models import Stock, FactorScore
from app.db.session import get_session_factory


def score(frame, weights):
    if abs(sum(weights.values()) - 1) > 1e-8 or any(v < 0 for v in weights.values()):
        raise ValueError('权重必须非负且合计1')
    if frame.symbol.duplicated().any() or not frame.symbol.str.fullmatch(r'\d{6}').all():
        raise ValueError('股票代码必须是唯一六位数字')
    frame = frame.copy()
    contributions = []
    for name, weight in weights.items():
        values = pd.to_numeric(frame[name], errors='coerce')
        if values.isna().any() or values.isin([float('inf'), -float('inf')]).any():
            raise ValueError(f'{name} 存在缺失或无效值；请先完成数据清洗')
        std = values.std(ddof=0)
        z = (values - values.mean()) / std if std > 0 else values * 0
        if name in {'pe_percentile','pb_percentile','volatility_60d'}:
            z = -z
        column = name + '_weighted_score'
        frame[column] = z * weight
        contributions.append(column)
    frame['composite_score'] = frame[contributions].sum(axis=1)
    frame = frame.sort_values(['composite_score','symbol'], ascending=[False,True])
    frame['rank'] = range(1,len(frame)+1)
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--data-date', type=date.fromisoformat, required=True)
    args = parser.parse_args()
    config = Path(__file__).resolve().parents[1] / 'data/seed/factors/final_factor_weights.json'
    weights = json.loads(config.read_text())['weights']
    scores = score(pd.read_csv(args.input, dtype={'symbol':str}), weights).head(30)
    factory = get_session_factory(get_settings().database_url)
    with factory.begin() as session:
        session.execute(delete(FactorScore).where(FactorScore.data_date==args.data_date))
        for r in scores.to_dict('records'):
            session.merge(Stock(symbol=r['symbol'], name=r['name'], industry=r.get('industry')))
        session.flush()
        for r in scores.to_dict('records'):
            values = {key:float(value) for key,value in r.items() if key in weights or key.endswith('_weighted_score')}
            session.add(FactorScore(symbol=r['symbol'], data_date=args.data_date, rank=r['rank'], composite_score=r['composite_score'], factor_values=values))
    print(f'已保存 {len(scores)} 只股票的 {args.data_date} 因子快照')

if __name__ == '__main__':
    main()
