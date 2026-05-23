"""
🛡️ Anti-Spam Middleware
حماية ضد السبام
"""

import time
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from config.settings import settings


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_times: Dict[int, list] = defaultdict(list)
        self.cooldown = settings.SPAM_COOLDOWN_SEC
        self.max_per_minute = settings.MAX_REQUESTS_PER_MIN

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()

        # Clean old timestamps
        self.user_times[user_id] = [
            t for t in self.user_times[user_id]
            if now - t < 60
        ]

        # Check rate limit
        if len(self.user_times[user_id]) >= self.max_per_minute:
            await event.answer(
                f"⚠️ أنت تُرسل رسائل بسرعة كبيرة!\n"
                f"يرجى الانتظار قليلاً ({self.cooldown} ثانية بين كل رسالة)"
            )
            return

        # Check cooldown
        if self.user_times[user_id]:
            last = self.user_times[user_id][-1]
            if now - last < self.cooldown:
                return  # Silent ignore

        self.user_times[user_id].append(now)
        return await handler(event, data)


"""
🔐 Auth Middleware
"""

from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.database import UserDB


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        user = await UserDB.get(user_id)

        if user and user.get("is_banned"):
            reason = user.get("ban_reason", "")
            await event.answer(
                f"🚫 <b>حسابك محظور</b>\n\n"
                f"{'السبب: ' + reason if reason else ''}\n\n"
                f"للتواصل: {settings.SUPPORT_USERNAME}"
            )
            return

        return await handler(event, data)


"""
📝 Logging Middleware
"""

import logging
from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user = event.from_user
            text_preview = ""
            if event.text:
                text_preview = event.text[:50]
            elif event.photo:
                text_preview = "[PHOTO]"
            elif event.voice:
                text_preview = "[VOICE]"
            elif event.document:
                text_preview = f"[FILE: {event.document.file_name}]"

            logger.info(
                f"MSG | user={user.id} | @{user.username} | {text_preview}"
            )

        return await handler(event, data)
