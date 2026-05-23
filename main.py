#!/usr/bin/env python3
"""
🤖 AI Telegram Bot - Main Entry Point
نظام الذكاء الاصطناعي المتكامل لتيليغرام
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from config.settings import settings
from handlers import (
    start_handler,
    chat_handler,
    image_handler,
    voice_handler,
    file_handler,
    admin_handler,
    subscription_handler,
)
from middlewares.anti_spam import AntiSpamMiddleware
from middlewares.auth import AuthMiddleware
from middlewares.logging_middleware import LoggingMiddleware
from utils.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot"""
    logger.info("🚀 Starting AI Telegram Bot...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Initialize bot and dispatcher
    bot = Bot(token=settings.TELEGRAM_TOKEN, parse_mode="HTML")

    # Use Redis storage if available, else memory
    try:
        storage = RedisStorage.from_url(settings.REDIS_URL)
        logger.info("✅ Redis storage connected")
    except Exception:
        storage = MemoryStorage()
        logger.warning("⚠️ Using memory storage (Redis not available)")

    dp = Dispatcher(storage=storage)

    # Register middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(AntiSpamMiddleware())
    dp.message.middleware(AuthMiddleware())

    # Register routers
    dp.include_router(start_handler.router)
    dp.include_router(chat_handler.router)
    dp.include_router(image_handler.router)
    dp.include_router(voice_handler.router)
    dp.include_router(file_handler.router)
    dp.include_router(subscription_handler.router)
    dp.include_router(admin_handler.router)

    logger.info("✅ All handlers registered")

    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
