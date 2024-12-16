import asyncio
import json
import signal

import aio_pika
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import TELEGRAM_BOT_TOKEN, get_rabbit_connection, redis
from services.tg_bot.handlers import callback_router, command_router, text_router
from services.tg_bot.texts import NEWS_TEXT
from services.tg_bot.utils.translator import translate_to_russian

logger = setup_logger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)


async def handle_ready_posts(message: aio_pika.IncomingMessage):
    data = json.loads(message.body.decode())
    translated_summary = translate_to_russian(data["news"])
    logger.info(
        f"Получено саммари {translated_summary}... для пользователя {data['user_id']}",
        correlation_id=data["correlation_id"],
    )
    await bot.send_message(
        chat_id=data["user_id"],
        text=NEWS_TEXT.format(
            feed_url=data["feed_url"],
            post_content=translated_summary,
            post_link=data["post_url"],
        ),
    )


async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск бота", correlation_id=correlation_id)

    # RabbitMQ connection
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue("rss.ready_posts", durable=True)
    logger.debug("Подключение к очереди rss.ready_posts", correlation_id=correlation_id)

    # Consume messages
    await queue.consume(handle_ready_posts)

    # Include routers
    dp.include_routers(command_router, text_router, callback_router)
    await dp.start_polling(bot)

    return connection  # Return connection for cleanup


async def shutdown(dp, connection):
    correlation_id = generate_correlation_id()
    logger.info("Завершение работы бота", correlation_id=correlation_id)

    # Close aiogram dispatcher
    await dp.storage.close()

    # Close RabbitMQ connection
    await connection.close()

    # Close bot session
    await bot.session.close()


if __name__ == "__main__":

    async def runner():
        connection = None
        try:
            connection = await main()
        except asyncio.CancelledError:
            logger.info("Received shutdown signal, cleaning up...")
        finally:
            if connection:
                await shutdown(dp, connection)

    # Create and set the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Add signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

    try:
        loop.run_until_complete(runner())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually")
    finally:
        # Cancel all pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
            try:
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass

        # Close the loop
        loop.close()
