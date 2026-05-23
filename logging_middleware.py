"""Logging Middleware"""
import logging
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: Dict[str, Any]):
        if isinstance(event, Message):
            user = event.from_user
            preview = event.text[:50] if event.text else "[media]"
            logger.info(f"MSG | {user.id} | @{user.username} | {preview}")
        return await handler(event, data)
