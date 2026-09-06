"""Public snapshot adapter. Never combine fresh fields with synthetic seed fields."""
from datetime import datetime
import math
import time

import httpx

from app.core.exceptions import MarketDataProviderError


def number(value):
    if value in (None, "", "-"):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


class PublicDashboardProvider:
    def __init__(self, timeout_seconds=12.0):
        self.timeout_seconds = timeout_seconds

    def rows(self, universe, fields, *, all_pages=False, sort="f6"):
        output = []
        for page in range(1, 101):
            params = {"pn": page, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                      "fid": sort, "fs": universe, "fields": fields}
            errors = []
            payload = None
            for host in ["https://push2.eastmoney.com", "https://82.push2.eastmoney.com"]:
                try:
                    with httpx.Client(timeout=self.timeout_seconds, transport=httpx.HTTPTransport(retries=1)) as client:
                        response = client.get(host + "/api/qt/clist/get", params=params)
                        response.raise_for_status()
                        payload = response.json()["data"]
                    if not payload or not isinstance(payload.get("diff"), list):
                        raise ValueError("empty or changed upstream schema")
                    break
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    errors.append(type(exc).__name__)
                    payload = None
            if payload is None:
                raise MarketDataProviderError("公开接口不可用：" + ", ".join(errors))
            output.extend(payload["diff"])
            if not all_pages or len(output) >= int(payload["total"]):
                return output
            time.sleep(.05)
        raise MarketDataProviderError("行情分页未完成，不保存部分市场统计。")

    def fetch(self, key):
        now = datetime.now()
        if key == "funds":
            rows = self.rows("m:90+t:2", "f14,f62", sort="f62")
            flows = [{"name": r["f14"], "net_inflow": number(r.get("f62"))} for r in rows]
            if not any(r["net_inflow"] is not None for r in flows):
                raise MarketDataProviderError("资金字段缺失，保留上次快照。")
            return {"northbound": {"net_inflow": None, "label": "北向资金净流入", "note": "当前数据源未提供可核验的净流入数据"}, "main_flow": flows}, "东方财富行业资金公开接口", now
        stocks = self.rows("m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23", "f12,f14,f3,f6", all_pages=True)
        indices = self.rows("m:1+s:2,m:0+t:5", "f12,f14,f2,f3", sort="f12")
        names = {"上证指数", "深证成指", "创业板指", "科创50"}
        indices = [{"name": r["f14"], "value": number(r.get("f2")), "change_percent": number(r.get("f3"))} for r in indices if r["f14"] in names]
        if len(indices) != 4 or any(i["value"] is None or i["change_percent"] is None for i in indices):
            raise MarketDataProviderError("指数快照不完整。")
        industries = self.rows("m:90+t:2", "f14,f3", sort="f3")
        changes = [number(r.get("f3")) for r in stocks]
        top = sorted(stocks, key=lambda r: number(r.get("f6")) or 0, reverse=True)[:20]
        data = {
            "indexes": indices,
            "industries": [{"name": r["f14"], "change_percent": number(r.get("f3")) or 0} for r in industries],
            "distribution": {"up": sum(v is not None and v > 0 for v in changes), "down": sum(v is not None and v < 0 for v in changes), "flat": sum(v == 0 for v in changes), "limit_up": None, "limit_down": None, "note": "涨跌停统计暂缺；不以统一10%阈值估算不同板块涨跌停。"},
            "top_turnover": [{"symbol": r["f12"], "name": r["f14"], "change_percent": number(r.get("f3")) or 0, "amount": number(r.get("f6")) or 0} for r in top],
        }
        return data, "东方财富公开接口；时间为采集时间，行业为东方财富板块口径", now
