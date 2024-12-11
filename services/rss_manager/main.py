import asyncio
import sys
import os

from config import init_db
from database.models import RssFeed, RssPost, Subscription

async def main():
    await init_db()

if __name__ == '__main__':
    asyncio.run(main())