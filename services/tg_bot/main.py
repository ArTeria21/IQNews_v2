import asyncio
import json
import signal

import aio_pika
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import TELEGRAM_BOT_TOKEN, get_rabbit_connection, redis
from services.tg_bot.handlers import callback_router, command_router, text_router
from services.tg_bot.texts import GET_NEWS_TEXT
from services.tg_bot.utils.translator import translate_to_russian

logger = setup_logger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)

# Dictionary to store per-user queues
user_queues = {}
# Lock to synchronize access to user_queues
queue_lock = asyncio.Lock()

async def process_user_queue(user_id: int):
    """
    Processes the message queue for a specific user.
    Sends one message and waits for 3 minutes before sending the next.
    """
    queue = user_queues[user_id]
    while True:
        message = await queue.get()
        try:
            # Send the message to the user
            await bot.send_message(
                chat_id=user_id,
                text=message['text']
            )
            logger.info(
                f"Sent news to user {user_id}",
                correlation_id=message.get('correlation_id')
            )
        except Exception as e:
            logger.error(
                f"Failed to send message to user {user_id}: {e}",
                correlation_id=message.get('correlation_id')
            )
        finally:
            # Wait for 3 minutes before sending the next message
            await asyncio.sleep(180)
            queue.task_done()

async def enqueue_message(user_id: int, text: str, correlation_id: str):
    """
    Enqueues a message for a specific user.
    If the user's queue doesn't exist, it creates one and starts the processing task.
    """
    async with queue_lock:
        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
            # Start the background task to process this user's queue
            asyncio.create_task(process_user_queue(user_id))
        await user_queues[user_id].put({'text': text, 'correlation_id': correlation_id})

async def handle_ready_posts(message: aio_pika.IncomingMessage):
    """
    Handles incoming messages from the 'rss.ready_posts' queue.
    Enqueues the message to the appropriate user's queue.
    """
    data = json.loads(message.body.decode())
    user_id = data["user_id"]
    correlation_id = data["correlation_id"]

    # Prepare the news message
    translated_summary = translate_to_russian(data["news"])
    news_text = GET_NEWS_TEXT(data["feed_url"], translated_summary, data["post_url"])

    # Enqueue the message for the user
    await enqueue_message(user_id, news_text, correlation_id)

async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск бота", correlation_id=correlation_id)

    # Establish RabbitMQ connection
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue("rss.ready_posts", durable=True)
    logger.debug("Подключение к очереди rss.ready_posts", correlation_id=correlation_id)

    # Start consuming messages from the queue
    await queue.consume(handle_ready_posts, no_ack=True)

    # Include all routers
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

    # Set up the event loop
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
