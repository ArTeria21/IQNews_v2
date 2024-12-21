import asyncio
import json
import signal
from typing import Optional

import aio_pika
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import (
    MINUTES_BETWEEN_POSTS,
    USE_WEBHOOK,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_PORT,
    WEBHOOK_URL,
    bot,
    dp,
    get_rabbit_connection,
)
from services.tg_bot.handlers import (
    admin_panel_router,
    callback_router,
    command_router,
    text_router,
)
from services.tg_bot.texts import GET_NEWS_TEXT
from services.tg_bot.utils.translator import translate_to_russian

logger = setup_logger(__name__)

# Message queue management
user_queues: dict = {}
queue_lock = asyncio.Lock()


async def process_user_queue(user_id: int) -> None:
    """Process messages in user's queue with rate limiting."""
    queue = user_queues[user_id]
    try:
        while True:
            message = await queue.get()
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message["text"],
                )
                logger.info(
                    f"Sent news to user {user_id}",
                    correlation_id=message.get("correlation_id"),
                )
            except Exception as e:
                logger.error(
                    f"Failed to send message to user {user_id}: {e}",
                    correlation_id=message.get("correlation_id"),
                )
            finally:
                await asyncio.sleep(60 * MINUTES_BETWEEN_POSTS)  # Rate limit
                queue.task_done()
    except asyncio.CancelledError:
        logger.info(f"User queue processing for {user_id} cancelled.")
        raise


async def enqueue_message(user_id: int, text: str, correlation_id: str) -> None:
    """Add message to user's queue, creating queue if needed."""
    async with queue_lock:
        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
            asyncio.create_task(process_user_queue(user_id))
        await user_queues[user_id].put(
            {"text": text, "correlation_id": correlation_id}
        )


async def handle_ready_posts(message: aio_pika.IncomingMessage) -> None:
    """Handle incoming RSS posts and queue for delivery."""
    async with message.process():
        data = json.loads(message.body.decode())
        translated_summary = translate_to_russian(data["news"])
        news_text = GET_NEWS_TEXT(
            data["feed_url"],
            translated_summary,
            data["post_url"],
            int(data["rank"]),
        )
        await enqueue_message(data["user_id"], news_text, data["correlation_id"])


async def handle_status_notification(message: aio_pika.IncomingMessage) -> None:
    """Handle user status change notifications."""
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(
            f"Пользователь {data['user_id']} получил уведомление о смене статуса на {data['status']}",
            correlation_id=data["correlation_id"],
        )
        try:
            await bot.send_message(
                chat_id=data["user_id"],
                text=f"Ваш статус был изменён на {data['status']}",
            )
        except Exception as e:
            logger.error(
                f"Failed to send status notification to user {data['user_id']}: {e}",
                correlation_id=data["correlation_id"],
            )


async def setup_rabbitmq() -> aio_pika.Connection:
    """Initialize RabbitMQ connections and queues."""
    connection = await get_rabbit_connection()
    channel = await connection.channel()

    # Declare queues
    ready_posts_queue = await channel.declare_queue("rss.ready_posts", durable=True)
    status_notification_queue = await channel.declare_queue(
        "user.status.notification", durable=True
    )

    # Set up consumers
    await ready_posts_queue.consume(handle_ready_posts, no_ack=False)
    await status_notification_queue.consume(handle_status_notification, no_ack=False)

    logger.info("RabbitMQ queues and consumers set up successfully.")
    return connection


async def on_startup() -> aio_pika.Connection:
    """Initialize bot, setup handlers and connections."""
    correlation_id = generate_correlation_id()
    logger.info("Starting bot initialization", correlation_id=correlation_id)

    # Setup RabbitMQ
    connection = await setup_rabbitmq()
    logger.info("Connected to RabbitMQ", correlation_id=correlation_id)

    # Setup routers
    dp.include_router(command_router)
    dp.include_router(text_router)
    dp.include_router(callback_router)
    dp.include_router(admin_panel_router)

    # Setup webhook if enabled
    if USE_WEBHOOK:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set up at {WEBHOOK_URL}", correlation_id=correlation_id)

        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        # Run the webhook server as an asyncio task
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=WEBHOOK_HOST, port=WEBHOOK_PORT)
        await site.start()
        logger.info(
            f"Webhook server started at http://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}",
            correlation_id=correlation_id,
        )
    else:
        # Start polling as a background task
        asyncio.create_task(dp.start_polling(bot))
        logger.info("Bot started polling.", correlation_id=correlation_id)

    return connection


async def on_shutdown(dp: Dispatcher, connection: Optional[aio_pika.Connection]) -> None:
    """Gracefully shutdown bot and close all connections."""
    correlation_id = generate_correlation_id()
    logger.info("Starting shutdown sequence", correlation_id=correlation_id)

    # Cancel all running tasks except current
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    logger.info("All running tasks have been requested to cancel.", correlation_id=correlation_id)

    # Wait for all tasks to be cancelled
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task resulted in an exception: {result}", correlation_id=correlation_id)

    logger.info("All tasks have been cancelled.", correlation_id=correlation_id)

    # Close webhook if enabled
    if USE_WEBHOOK:
        try:
            await bot.delete_webhook()
            logger.info("Webhook deleted successfully.", correlation_id=correlation_id)
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}", correlation_id=correlation_id)

    # Close storage
    try:
        await dp.storage.close()
        logger.info("Storage closed successfully.", correlation_id=correlation_id)
    except Exception as e:
        logger.error(f"Failed to close storage: {e}", correlation_id=correlation_id)

    # Close RabbitMQ connection
    if connection and not connection.is_closed:
        try:
            await connection.close()
            logger.info("RabbitMQ connection closed successfully.", correlation_id=correlation_id)
        except Exception as e:
            logger.error(f"Failed to close RabbitMQ connection: {e}", correlation_id=correlation_id)

    # Close bot session
    try:
        await bot.session.close()
        logger.info("Bot session closed successfully.", correlation_id=correlation_id)
    except Exception as e:
        logger.error(f"Failed to close bot session: {e}", correlation_id=correlation_id)

    logger.info("Shutdown sequence completed.", correlation_id=correlation_id)


async def main():
    """Main entry point for the Telegram bot."""
    connection = None

    async def shutdown_handler():
        """Handles shutdown signals."""
        await on_shutdown(dp, connection)
        asyncio.get_event_loop().stop()

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown_handler()))

    try:
        connection = await on_startup()
        logger.info("Bot is up and running.")
        # Keep the program running indefinitely
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if connection and not connection.is_closed:
            await connection.close()
            logger.info("RabbitMQ connection closed in finally block.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.exception(f"Bot terminated due to an exception: {e}")
