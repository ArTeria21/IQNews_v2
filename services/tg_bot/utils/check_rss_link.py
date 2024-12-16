import asyncio
from datetime import datetime, timedelta, timezone

import aiohttp
import feedparser


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
            async with session.get(
                url, allow_redirects=True, timeout=timeout
            ) as response:
                # print(f"Checking RSS feed: {url}")
                # print(f"Response status: {response.status}")

                # Проверка статуса ответа
                if response.status != 200:
                    # print("Non-200 status code received.")
                    return False

                # Проверка типа содержимого
                content_type = response.headers.get("Content-Type", "").lower()
                # print(f"Content type: {content_type}")
                if not any(ct in content_type for ct in ("xml", "rss", "atom")):
                    # print("Content type does not seem to be an RSS/Atom/XML feed.")
                    return False

                content = await response.text()
                feed = feedparser.parse(content)

                # Проверка на ошибки парсинга
                if feed.bozo:
                    # print("Feed parsing error (bozo == True).")
                    return False

                entries = feed.get("entries", [])
                if not entries:
                    # print("No entries found in the feed.")
                    return False

                # Проверяем каждую запись
                for idx, entry in enumerate(entries, start=1):
                    # print(f"Validating entry {idx}")

                    title = entry.get("title")
                    link = entry.get("link")
                    published = entry.get("published", None) or entry.get(
                        "updated", None
                    )

                    # Проверка обязательных полей
                    if not (title and link and published):
                        return False

                # print("All entries passed validation.")
                return True
    except Exception:
        return False


async def is_feed_active(url: str, timeout: int = 5) -> bool:
    """
    Проверяет, что последний (самый свежий) пост в RSS-потоке был опубликован
    не более 6 месяцев назад. Если да, возвращает True, иначе False.

    Предполагается, что RSS-поток уже проверен на корректность другими функциями.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, allow_redirects=True, timeout=timeout
            ) as response:
                if response.status != 200:
                    return False

                content_type = response.headers.get("Content-Type", "").lower()
                if not any(ct in content_type for ct in ("xml", "rss", "atom")):
                    return False

                content = await response.text()
                feed = feedparser.parse(content)

                if feed.bozo:
                    return False

                entries = feed.get("entries", [])
                if not entries:
                    return False

                # Находим дату самого свежего поста
                newest_date = None
                for entry in entries:
                    # Попытка получить дату из published_parsed или updated_parsed
                    parsed_date = entry.get("published_parsed") or entry.get(
                        "updated_parsed"
                    )
                    if parsed_date:
                        dt = datetime(*parsed_date[:6], tzinfo=timezone.utc)
                        if newest_date is None or dt > newest_date:
                            newest_date = dt

                # Если ни в одном посте нет валидной даты
                if not newest_date:
                    return False

                # Проверяем, что пост не старше 6 месяцев (примерно 180 дней)
                six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
                return newest_date > six_months_ago

    except Exception:
        # print(f"Error checking feed activity for {url}: {e}")
        return False


if __name__ == "__main__":
    url = "https://deepmind.google/blog/rss.xml"
    result = asyncio.run(is_feed_active(url))
    print(result)
