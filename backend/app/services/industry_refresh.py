"""Compute industry rotation from public Shenwan daily prices."""
from datetime import date, datetime
import httpx
import pandas as pd
from sqlalchemy import select
from app.core.config import get_settings
from app.db.models import IndustryRotation
from app.db.session import get_session_factory


def calculate_rotation(history, code, name):
    frame = pd.DataFrame(history)
    frame['close'] = pd.to_numeric(frame['close'], errors='coerce')
    frame = frame.dropna(subset=['close']).sort_values('date').drop_duplicates('date')
    if len(frame) < 61 or (frame['close'] <= 0).any():
        raise ValueError(f'{name}: 有效历史行情不足61天')
    return dict(industry_code=code, industry_name=name, data_date=date.fromisoformat(str(frame.iloc[-1]['date'])[:10]), latest_close=float(frame.iloc[-1]['close']), return_1m=float(frame.iloc[-1]['close']/frame.iloc[-21]['close']-1), return_3m=float(frame.iloc[-1]['close']/frame.iloc[-61]['close']-1))


def refresh_rotation():
    factory = get_session_factory(get_settings().database_url)
    with factory() as session:
        old = session.scalars(select(IndustryRotation).order_by(IndustryRotation.data_date.desc())).all()
        targets = {r.industry_code: r.industry_name for r in old}
    records = []
    with httpx.Client(timeout=12, transport=httpx.HTTPTransport(retries=1), headers={'Referer': 'https://www.swsresearch.com/', 'User-Agent': 'Mozilla/5.0'}) as client:
        for code, name in targets.items():
            response = client.get('https://www.swsresearch.com/institute-sw/api/index_publish/trend/', params={'swindexcode': code.split('.')[0], 'period': 'DAY'})
            response.raise_for_status()
            data = response.json()['data']
            history = [{'date': r['bargaindate'][:10], 'close': r['closeindex']} for r in data]
            records.append(calculate_rotation(history, code, name))
    if not records:
        raise ValueError('没有可刷新行业')
    frame = pd.DataFrame(records)
    if frame.data_date.nunique() != 1:
        raise ValueError('行业数据日期不一致，保留旧快照')
    frame['rank_1m'] = frame.return_1m.rank(ascending=False, method='first').astype(int)
    frame['rank_3m'] = frame.return_3m.rank(ascending=False, method='first').astype(int)
    strong, weak = round(len(frame)*.33), round(len(frame)*.67)
    with factory.begin() as session:
        for record in frame.to_dict('records'):
            a,b = record['rank_1m'], record['rank_3m']
            label = '持续强势' if a<=strong and b<=strong else '短期转强' if a<=strong and b>weak else '中期强势' if a>weak and b<=strong else '持续走弱' if a>weak and b>weak else '震荡中性'
            row = session.scalar(select(IndustryRotation).where(IndustryRotation.industry_code==record['industry_code'], IndustryRotation.data_date==record['data_date']))
            if row is None:
                row = IndustryRotation(**record, rotation_type=label, generated_at=datetime.now())
                session.add(row)
            else:
                for key,value in record.items():
                    setattr(row,key,value)
                row.rotation_type, row.generated_at = label, datetime.now()
