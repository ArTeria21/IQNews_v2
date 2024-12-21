import asyncio

import pytest

from services.tg_bot.utils.check_rss_link import (is_feed_active,
                                                  is_valid_rss_feed)

# Тестовые данные
test_cases_is_valid_rss_feed = [
    ("https://nplus1.ru/rss", True),
    ("Test", False),
    ("https://github.com/", False),
    ("https://www.example.com/rss", False),
    ("", False),
    (52, False),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected_result", test_cases_is_valid_rss_feed)
async def test_is_valid_rss_feed(url, expected_result):
    result = await is_valid_rss_feed(url)
    assert result == expected_result

test_cases_is_feed_active = [
    ("https://nplus1.ru/rss", True),
    ("https://pandio.com/feed/", False),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected_result", test_cases_is_feed_active)
async def test_is_feed_active(url, expected_result):
    result = await is_feed_active(url)
    assert result == expected_result