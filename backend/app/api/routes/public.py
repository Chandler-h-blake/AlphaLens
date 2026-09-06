from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from app.core.config import get_settings


router = APIRouter(include_in_schema=False)

PUBLIC_PATHS = ("/", "/factors", "/research", "/industry", "/market")


def _site_url(request: Request) -> str:
    configured_url = get_settings().public_site_url
    if configured_url:
        return configured_url.rstrip("/")
    forwarded_scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme).split(",", maxsplit=1)[0].strip()
    forwarded_host = request.headers.get("X-Forwarded-Host", request.headers.get("Host", request.url.netloc)).split(",", maxsplit=1)[0].strip()
    return f"{forwarded_scheme}://{forwarded_host}".rstrip("/")


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt(request: Request) -> PlainTextResponse:
    base_url = _site_url(request)
    return PlainTextResponse(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")


@router.get("/sitemap.xml")
def sitemap_xml(request: Request) -> Response:
    base_url = _site_url(request)
    locations = "".join(f"<url><loc>{escape(base_url + path)}</loc></url>" for path in PUBLIC_PATHS)
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locations}</urlset>'
    return Response(content=body, media_type="application/xml")
