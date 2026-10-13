import httpx
import pytest

from unify.services.fetch_meta import fetch_metadata


@pytest.mark.asyncio
async def test_fetches_title_and_description() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text=(
                "<html><head><title> Example title </title>"
                '<meta name="description" content=" Example description "></head></html>'
            ),
        )
    )

    result = await fetch_metadata("https://example.com", transport=transport)

    assert result == ("Example title", "Example description")


@pytest.mark.asyncio
async def test_fetches_title_without_description() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"Content-Type": "text/html; charset=utf-8"},
            text="<title>Only title</title>",
        )
    )

    assert await fetch_metadata("https://example.com", transport=transport) == ("Only title", "")


@pytest.mark.asyncio
async def test_fetches_open_graph_description_case_insensitively() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text='<meta PROPERTY="OG:DESCRIPTION" content="Open Graph description">',
        )
    )

    assert await fetch_metadata("https://example.com", transport=transport) == (
        "",
        "Open Graph description",
    )


@pytest.mark.asyncio
async def test_non_html_returns_empty_metadata() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, headers={"Content-Type": "application/json"}, text="{}")
    )

    assert await fetch_metadata("https://example.com", transport=transport) == ("", "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        httpx.TimeoutException("timed out"),
        httpx.ConnectError("connection failed"),
    ],
)
async def test_http_errors_return_empty_metadata(error: httpx.HTTPError) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise error

    transport = httpx.MockTransport(fail)

    assert await fetch_metadata("https://example.com", transport=transport) == ("", "")


@pytest.mark.asyncio
async def test_file_url_is_rejected() -> None:
    assert await fetch_metadata("file:///etc/passwd") == ("", "")


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://10.0.0.1/"])
async def test_private_addresses_are_rejected(url: str) -> None:
    assert await fetch_metadata(url) == ("", "")


@pytest.mark.asyncio
async def test_redirect_to_private_address_is_rejected() -> None:
    requested_urls: list[str] = []

    def redirect_private(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/"})

    transport = httpx.MockTransport(redirect_private)

    assert await fetch_metadata("https://example.com", transport=transport) == ("", "")
    assert requested_urls == ["https://example.com"]
