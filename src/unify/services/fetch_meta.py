import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
USER_AGENT = "unify/0.1 (+https://github.com/Bidex-cmyk/unify)"


def _validate_public_http_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use HTTP or HTTPS and include a hostname")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("URL hostname did not resolve")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("URL resolves to a non-public IP address")


async def _guard_request(request: httpx.Request) -> None:
    await asyncio.to_thread(_validate_public_http_url, str(request.url))


async def fetch_metadata(
    url: str,
    *,
    timeout: float = 8.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[str, str]:
    try:
        await asyncio.to_thread(_validate_public_http_url, url)
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            transport=transport,
            event_hooks={"request": [_guard_request]},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", "").lower():
                return "", ""

            soup = BeautifulSoup(response.text, "html.parser")
            title_element = soup.find("title")
            title = title_element.get_text(" ", strip=True)[:300] if title_element else ""

            description = ""
            for meta in soup.find_all("meta"):
                name = str(meta.get("name", "")).casefold()
                property_name = str(meta.get("property", "")).casefold()
                if name == "description" or property_name == "og:description":
                    description = str(meta.get("content", "")).strip()[:500]
                    break
            return title, description
    except Exception:
        logger.warning("Failed to fetch bookmark metadata", exc_info=True)
        return "", ""
