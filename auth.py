"""Auth Middleware"""
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from utils.database import UserDB
from config.settings import settings


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: Dict[str, Any]):
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)
        user_id = event.from_user.id
        user = await UserDB.get(user_id)
        if user and user.get("is_banned"):
            reason = user.get("ban_reason", "")
            await event.answer(f"🚫 <b>حسابك محظور</b>\n{'السبب: ' + reason if reason else ''}\nللتواصل: {settings.SUPPORT_USERNAME}")
            return
        return await handler(event, data)
