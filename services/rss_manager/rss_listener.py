import asyncio
import aiohttp
import feedparser
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from database.models import RssFeed, RssPost

from config import async_session_factory
from utils.web_parser import fetch_article_text


class RSSListener:
    def __init__(self, max_concurrent=20):
        """
        :param session_factory: фабрика асинхронных сессий (async_sessionmaker)
        :param max_concurrent: максимальное число одновременных запросов к RSS
        """
        self.session_factory = async_session_factory
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_rss_content(self, url: str) -> str:
        """Асинхронно скачивает содержимое RSS по URL."""
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    return await response.text()

    async def fetch_and_update_feed(self, feed: RssFeed):
        """
        Забирает RSS поток, парсит его и добавляет новые посты в базу данных, 
        если они новее последнего зафиксированного поста.
        """
        async with self.session_factory() as session:
            # Получаем актуальный feed из БД (на случай изменения пока шёл запрос)
            db_feed = await session.get(RssFeed, feed.feed_id)
            if db_feed is None:
                return  # Лента могла быть удалена
            
            try:
                content = await self.fetch_rss_content(db_feed.url)
            except Exception as e:
                # Можно логировать ошибку
                return
            
            parsed = feedparser.parse(content)
            if not parsed.entries:
                return  # Нет записей в ленте
            
            last_post_date = db_feed.last_post_date or datetime.min
            new_posts = []

            for entry in parsed.entries:
                # Извлекаем дату публикации
                # feedparser поддерживает published_parsed, проверим его
                published_dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed is not None:
                    published_dt = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed is not None:
                    published_dt = datetime(*entry.updated_parsed[:6])
                
                if published_dt is None:
                    # Если нет даты, пропускаем, или можно установить datetime.now()
                    continue
                
                # Проверяем, новее ли пост
                if published_dt > last_post_date:
                    # Собираем данные поста
                    title = entry.title if hasattr(entry, 'title') else 'No Title'
                    link = entry.link if hasattr(entry, 'link') else ''
                    content = entry.summary if hasattr(entry, 'summary') else ''
                    
                    if len(content.split()) < 150:
                        content = await fetch_article_text(link)
                        if not content:
                            continue
                    
                    content = content.replace('\n', ' ')
                    
                    # Создаём новый объект RssPost
                    new_post = RssPost(
                        feed_id=db_feed.feed_id,
                        title=title,
                        content=content,
                        link=link,
                        published_at=published_dt
                    )
                    new_posts.append(new_post)
            
            if new_posts:
                session.add_all(new_posts)
                # Обновляем last_post_date
                # Находим максимальную дату из новых постов
                max_date = max(post.published_at for post in new_posts)
                db_feed.last_post_date = max_date
                await session.commit()

    async def check_feeds(self):
        """
        Проверяет все RssFeed в базе данных, асинхронно обновляет их.
        """
        async with self.session_factory() as session:
            feeds = (await session.execute(select(RssFeed))).scalars().all()
        
        # Запускаем таски для всех лент
        tasks = [asyncio.create_task(self.fetch_and_update_feed(feed)) for feed in feeds]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    listener = RSSListener()
    asyncio.run(listener.check_feeds())