from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Protocol
from urllib.parse import urljoin
import html
import re

import httpx

from app.core.config import Settings
from app.core.exceptions import MarketDataProviderError


CHINA_TZ = timezone(timedelta(hours=8))
SOURCE_NAME = "东方财富公开行情与公告接口"


@dataclass(frozen=True)
class FetchedQuote:
    symbol: str
    name: str
    latest_price: float
    change_amount: float | None
    change_percent: float | None
    open_price: float | None
    high_price: float | None
    low_price: float | None
    volume: float | None
    amount: float | None
    total_market_cap: float | None
    main_net_inflow: float | None
    as_of: datetime
    source: str = SOURCE_NAME


@dataclass(frozen=True)
class FetchedAnnouncement:
    article_id: str
    title: str
    category: str | None
    published_at: datetime | None
    url: str | None
    source: str = "东方财富网 · 巨潮公告"


class MarketDataProvider(Protocol):
    def fetch_quote(self, symbol: str) -> FetchedQuote: ...

    def fetch_announcements(self, symbol: str, limit: int) -> list[FetchedAnnouncement]: ...


class EastMoneyPublicProvider:
    """Small, dependency-free adapter for the public endpoints used in the prior internship work."""

    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        self.timeout_seconds = settings.market_data_timeout_seconds
        self.transport = transport

    def fetch_quote(self, symbol: str) -> FetchedQuote:
        normalized = _normalize_symbol(symbol)
        fields = "f43,f44,f45,f46,f47,f48,f57,f58,f116,f124,f140,f169,f170"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        try:
            with self._client() as client:
                response = client.get(url, params={"secid": _security_id(normalized), "fields": fields})
                response.raise_for_status()
                data = response.json().get("data")
        except (httpx.HTTPError, ValueError):
            return self._fetch_tencent_quote(normalized)
        if not isinstance(data, dict) or not data.get("f57"):
            return self._fetch_tencent_quote(normalized)

        latest_price = _scaled(data.get("f43"))
        if latest_price is None:
            raise MarketDataProviderError("实时行情接口未返回最新价。")
        return FetchedQuote(
            symbol=str(data["f57"]).zfill(6),
            name=str(data.get("f58") or normalized),
            latest_price=latest_price,
            change_amount=_scaled(data.get("f169")),
            change_percent=_scaled(data.get("f170")),
            open_price=_scaled(data.get("f46")),
            high_price=_scaled(data.get("f44")),
            low_price=_scaled(data.get("f45")),
            volume=_number(data.get("f47")),
            amount=_number(data.get("f48")),
            total_market_cap=_number(data.get("f116")),
            main_net_inflow=_number(data.get("f140")),
            as_of=_market_datetime(data.get("f124")),
        )

    def fetch_announcements(self, symbol: str, limit: int) -> list[FetchedAnnouncement]:
        normalized = _normalize_symbol(symbol)
        today = datetime.now(CHINA_TZ)
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        params = {
            "sr": "-1",
            "page_size": str(limit),
            "page_index": "1",
            "ann_type": "A",
            "stock_list": normalized,
            "f_node": "0",
            "begin_time": (today - timedelta(days=90)).strftime("%Y%m%d"),
            "end_time": today.strftime("%Y%m%d"),
        }
        try:
            with self._client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                items = response.json().get("data", {}).get("list", [])
        except (httpx.HTTPError, ValueError):
            return self._fetch_sina_news(normalized, limit)
        if not isinstance(items, list):
            return self._fetch_sina_news(normalized, limit)

        records: list[FetchedAnnouncement] = []
        for item in items:
            article_id = str(item.get("art_code") or "").strip()
            title = str(item.get("title_ch") or item.get("title") or "").strip()
            if not article_id or not title:
                continue
            columns = item.get("columns") or []
            category = str(columns[0].get("column_name") or "").strip() if columns else None
            records.append(
                FetchedAnnouncement(
                    article_id=article_id,
                    title=title,
                    category=category or None,
                    published_at=_parse_notice_datetime(item.get("notice_date") or item.get("display_time")),
                    url=f"https://data.eastmoney.com/notices/detail/{normalized}/{article_id}.html",
                )
            )
        return records or self._fetch_sina_news(normalized, limit)

    def _fetch_tencent_quote(self, symbol: str) -> FetchedQuote:
        market_prefix = "sh" if symbol.startswith("6") else "sz"
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        try:
            with self._client() as client:
                response = client.get(url, params={"param": f"{market_prefix}{symbol},day,,,5,qfq"})
                response.raise_for_status()
                payload = response.json().get("data", {}).get(f"{market_prefix}{symbol}", {})
                values = payload.get("qt", {}).get(f"{market_prefix}{symbol}", [])
        except (httpx.HTTPError, ValueError) as error:
            raise MarketDataProviderError(f"实时行情接口请求失败，腾讯备用源也不可用：{error}") from error
        if not isinstance(values, list) or len(values) < 35 or _number(values[3]) is None:
            raise MarketDataProviderError("腾讯财经备用行情接口未返回有效股票数据。")
        amount_parts = str(values[35]).split("/") if len(values) > 35 else []
        market_cap_in_hundred_millions = _number(values[44]) if len(values) > 44 else None
        return FetchedQuote(
            symbol=str(values[2]).zfill(6),
            name=str(values[1]),
            latest_price=float(values[3]),
            change_amount=_number(values[31]) if len(values) > 31 else None,
            change_percent=_number(values[32]) if len(values) > 32 else None,
            open_price=_number(values[5]) if len(values) > 5 else None,
            high_price=_number(values[33]) if len(values) > 33 else None,
            low_price=_number(values[34]) if len(values) > 34 else None,
            volume=_number(values[6]) if len(values) > 6 else None,
            amount=_number(amount_parts[-1]) if amount_parts else None,
            total_market_cap=market_cap_in_hundred_millions * 100_000_000 if market_cap_in_hundred_millions is not None else None,
            main_net_inflow=None,
            as_of=_parse_tencent_datetime(values[30] if len(values) > 30 else None),
            source="腾讯财经公开行情接口（东方财富不可用时自动切换）",
        )

    def _fetch_sina_news(self, symbol: str, limit: int) -> list[FetchedAnnouncement]:
        market_prefix = "SH" if symbol.startswith("6") else "SZ"
        url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{market_prefix}{symbol}.phtml"
        try:
            with self._client() as client:
                response = client.get(url)
                response.raise_for_status()
                response.encoding = "gbk"
                content = response.text
        except httpx.HTTPError:
            return []
        match = re.search(r'id="datelist"[^>]*>(.*?)</ul>', content, re.DOTALL)
        section = match.group(1) if match else content
        records: list[FetchedAnnouncement] = []
        for part in section.split("<br>"):
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})(?:&nbsp;|\s)+(\d{2}:\d{2})", part)
            href_match = re.search(r"href=[\"']([^\"']*)[\"']", part)
            title_match = re.search(r"<a[^>]*>(.*?)</a>", part, re.DOTALL)
            if not date_match or not href_match or not title_match:
                continue
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            title = html.unescape(title)
            href = urljoin(url, href_match.group(1))
            if not title or any(item.url == href for item in records):
                continue
            records.append(
                FetchedAnnouncement(
                    article_id=sha256(href.encode("utf-8")).hexdigest()[:32],
                    title=title,
                    category="个股资讯",
                    published_at=_parse_notice_datetime(f"{date_match.group(1)} {date_match.group(2)}"),
                    url=href,
                    source="新浪财经公开个股资讯（东方财富不可用时自动切换）",
                )
            )
            if len(records) >= limit:
                break
        return records

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout_seconds,
            trust_env=False,
            transport=self.transport,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            },
        )


class DisabledMarketDataProvider:
    def fetch_quote(self, symbol: str) -> FetchedQuote:
        raise MarketDataProviderError("在线行情服务未启用。")

    def fetch_announcements(self, symbol: str, limit: int) -> list[FetchedAnnouncement]:
        raise MarketDataProviderError("在线行情服务未启用。")


def build_market_data_provider(settings: Settings) -> MarketDataProvider:
    if settings.market_data_provider == "eastmoney_public":
        return EastMoneyPublicProvider(settings)
    return DisabledMarketDataProvider()


def _normalize_symbol(value: str) -> str:
    symbol = value.strip()
    if len(symbol) != 6 or not symbol.isdigit():
        raise MarketDataProviderError("股票代码必须是六位数字。")
    return symbol


def _security_id(symbol: str) -> str:
    market = "1" if symbol.startswith("6") else "0"
    return f"{market}.{symbol}"


def _number(value: object) -> float | None:
    if value is None or value == "-":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scaled(value: object) -> float | None:
    numeric = _number(value)
    return numeric / 100 if numeric is not None else None


def _market_datetime(value: object) -> datetime:
    try:
        timestamp = int(str(value))
        if timestamp > 0:
            return datetime.fromtimestamp(timestamp, tz=CHINA_TZ).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        pass
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def _parse_notice_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    for format_string in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if " " in text else text[:10], format_string)
        except ValueError:
            continue
    return None


def _parse_tencent_datetime(value: object) -> datetime:
    try:
        return datetime.strptime(str(value), "%Y%m%d%H%M%S")
    except ValueError:
        return datetime.now(CHINA_TZ).replace(tzinfo=None)
