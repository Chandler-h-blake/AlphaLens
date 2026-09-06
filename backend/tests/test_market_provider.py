import json

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
