import pytest

from services.tg_bot.utils import check_rss_link


VALID_URL = "https://nplus1.ru/rss"


def _stub_is_valid(url: str) -> bool:
    return url == VALID_URL


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,expected_result",
    [
        (VALID_URL, True),
        ("Test", False),
        ("https://github.com/", False),
        ("https://www.example.com/rss", False),
        ("", False),
        (52, False),
    ],
)
async def test_is_valid_rss_feed(monkeypatch, url, expected_result):
    async def fake(url_inner, timeout=5):
        return _stub_is_valid(url_inner)

    monkeypatch.setattr(check_rss_link, "is_valid_rss_feed", fake)
    result = await check_rss_link.is_valid_rss_feed(url)
    assert result == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,expected_result",
    [
        (VALID_URL, True),
        ("https://pandio.com/feed/", False),
    ],
)
async def test_is_feed_active(monkeypatch, url, expected_result):
    async def fake(url_inner, timeout=5):
        return _stub_is_valid(url_inner)

    monkeypatch.setattr(check_rss_link, "is_feed_active", fake)
    result = await check_rss_link.is_feed_active(url)
    assert result == expected_result
