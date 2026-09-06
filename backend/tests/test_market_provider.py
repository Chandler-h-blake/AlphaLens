import json
from datetime import date, timedelta

import httpx

from app.core.config import Settings
from app.market.eastmoney_provider import EastMoneyPublicProvider


def test_quote_falls_back_to_tencent_when_eastmoney_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "push2.eastmoney.com":
            return httpx.Response(503, request=request)
        assert request.url.host == "web.ifzq.gtimg.cn"
        values = ["" for _ in range(45)]
        values[1], values[2], values[3], values[5], values[6] = "巨人网络", "002558", "29.56", "27.90", "1455411"
        values[30], values[31], values[32], values[33], values[34] = "20260710161430", "1.24", "4.38", "29.88", "27.40"
        values[35], values[44] = "29.56/1455411/4206352830", "561.81"
        payload = {"data": {"sz002558": {"qt": {"sz002558": values}}}}
        return httpx.Response(200, json=payload, request=request)

    provider = EastMoneyPublicProvider(Settings(), transport=httpx.MockTransport(handler))
    quote = provider.fetch_quote("002558")

    assert quote.latest_price == 29.56
    assert quote.change_percent == 4.38
    assert quote.amount == 4206352830
    assert "腾讯财经" in quote.source


def test_announcements_fall_back_to_sina_news_when_eastmoney_fails() -> None:
    html = '''<ul id="datelist">&nbsp;&nbsp;2026-07-10&nbsp;10:30&nbsp;&nbsp;<a href="https://finance.example/item">巨人网络发布新公告</a><br></ul>'''

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "np-anotice-stock.eastmoney.com":
            return httpx.Response(503, request=request)
        assert request.url.host == "vip.stock.finance.sina.com.cn"
        return httpx.Response(200, content=html.encode("gbk"), request=request)

    provider = EastMoneyPublicProvider(Settings(), transport=httpx.MockTransport(handler))
    announcements = provider.fetch_announcements("002558", 3)

    assert len(announcements) == 1
    assert announcements[0].title == "巨人网络发布新公告"
    assert announcements[0].category == "个股资讯"


def test_daily_history_parses_close_and_turnover() -> None:
    start = date(2026, 1, 1)
    lines = [
        f"{start + timedelta(days=index)},10,{10 + index / 10},11,9,1000,10000,2,1,.1,{1 + index / 100}"
        for index in range(70)
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "push2his.eastmoney.com"
        return httpx.Response(200, json={"data": {"klines": lines}}, request=request)

    provider = EastMoneyPublicProvider(Settings(), transport=httpx.MockTransport(handler))
    bars = provider.fetch_daily_history("002558")

    assert len(bars) == 70
    assert bars[-1].close == 16.9
    assert bars[-1].turnover_rate == 1.69


def test_daily_history_falls_back_to_tencent_volume_ratio() -> None:
    start = date(2026, 1, 1)
    lines = [
        [(start + timedelta(days=index)).isoformat(), "10", str(10 + index / 10), "11", "9", str(1000 + index)]
        for index in range(70)
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "push2his.eastmoney.com":
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"data": {"sz002558": {"qfqday": lines}}}, request=request)

    provider = EastMoneyPublicProvider(Settings(), transport=httpx.MockTransport(handler))
    bars = provider.fetch_daily_history("002558")

    assert len(bars) == 70
    assert bars[-1].turnover_rate == 1069
    assert "成交量比率" in bars[-1].source
