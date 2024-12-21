import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp
import feedparser

logger = logging.getLogger(__name__)


async def is_valid_rss_feed(url: str, timeout: int = 5) -> bool:
    """
    Проверяет корректность RSS-потока по заданному URL.

    Критерии валидации:
    1. Успешный ответ с кодом 200.
    2. Корректный MIME тип (содержит 'xml', 'rss' или 'atom').
    3. Корректный RSS-поток без ошибок парсинга (feed.bozo == 0).
    4. Наличие хотя бы одной записи (entry) в потоке.
    5. Каждая запись должна содержать:
        - title
        - link
        - summary или content
        - дату публикации (published или updated)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=timeout) as response:
                OK_STATUS_CODE = 200
                if response.status != OK_STATUS_CODE:
                    logger.debug(f"URL {url} returned status code {response.status}.")
                    return False

                content_type = response.headers.get("Content-Type", "").lower()
                if not any(ct in content_type for ct in ("xml", "rss", "atom")):
                    logger.debug(f"URL {url} has unsupported Content-Type: {content_type}.")
                    return False

                content = await response.text()
                feed = feedparser.parse(content)

                if feed.bozo:
                    logger.debug(f"Feed parsing error for URL {url}: {feed.bozo_exception}.")
                    return False

                entries = feed.get("entries", [])
                if not entries:
                    logger.debug(f"No entries found in feed from URL {url}.")
                    return False

                for entry in entries:
                    title = entry.get("title")
                    link = entry.get("link")
                    published = entry.get("published") or entry.get("updated")
                    if not (title and link and published):
                        logger.debug(f"Entry missing required fields in feed from URL {url}.")
                        return False

                return True
    except Exception as e:
        logger.error(f"Exception occurred while validating RSS feed {url}: {e}")
        return False


async def is_feed_active(url: str, timeout: int = 5) -> bool:
    """
    Проверяет, что последний (самый свежий) пост в RSS-потоке был опубликован
    не более 6 месяцев назад. Если да, возвращает True, иначе False.

    Предполагается, что RSS-поток уже проверен на корректность другими функциями.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=timeout) as response:
                OK_STATUS_CODE = 200
                if response.status != OK_STATUS_CODE:
                    logger.debug(f"URL {url} returned status code {response.status}.")
                    return False

                content_type = response.headers.get("Content-Type", "").lower()
                if not any(ct in content_type for ct in ("xml", "rss", "atom")):
                    logger.debug(f"URL {url} has unsupported Content-Type: {content_type}.")
                    return False

                content = await response.text()
                feed = feedparser.parse(content)

                if feed.bozo:
                    logger.debug(f"Feed parsing error for URL {url}: {feed.bozo_exception}.")
                    return False

                entries = feed.get("entries", [])
                if not entries:
                    logger.debug(f"No entries found in feed from URL {url}.")
                    return False

                # Находим дату самого свежего поста
                newest_date = None
                for entry in entries:
                    parsed_date = entry.get("published_parsed") or entry.get("updated_parsed")
                    if parsed_date:
                        dt = datetime(*parsed_date[:6], tzinfo=timezone.utc)
                        if newest_date is None or dt > newest_date:
                            newest_date = dt

                if not newest_date:
                    logger.debug(f"No valid publication dates found in feed from URL {url}.")
                    return False

                six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
                is_active = newest_date > six_months_ago
                logger.debug(f"Feed from URL {url} is_active: {is_active}.")
                return is_active
    except Exception as e:
        logger.error(f"Exception occurred while checking if feed is active {url}: {e}")
        return False


if __name__ == "__main__":
    url = "https://deepmind.google/blog/rss.xml"
    result = asyncio.run(is_feed_active(url))
    print(result)
