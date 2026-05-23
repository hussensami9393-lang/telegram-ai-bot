"""
💬 Chat Handler - Main AI conversation
معالج الدردشة الرئيسي مع الذكاء الاصطناعي
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from services.ai_service import chat_with_ai, translate_text, summarize_text
from utils.database import ConversationDB, UsageDB, UserDB
from config.settings import settings

router = Router()

TYPING_MSG = "⏳ جاري التفكير..."


def limit_reached_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 ترقية للبرو", callback_data="subscription")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu")],
    ])


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message):
    """Handle all text messages"""
    user_id = message.from_user.id
    text = message.text.strip()

    # Check usage limit
    if not await UsageDB.can_use(user_id, "message"):
        await message.answer(
            f"⚠️ <b>تجاوزت حد الرسائل اليومي ({settings.FREE_DAILY_MESSAGES} رسائل)</b>\n\n"
            "قم بالترقية إلى <b>Pro</b> للحصول على رسائل غير محدودة! 🚀",
            reply_markup=limit_reached_keyboard()
        )
        return

    # Show typing
    processing = await message.answer(TYPING_MSG)

    try:
        # Check for special commands in text
        lower_text = text.lower()

        # Translation request
        if any(w in lower_text for w in ["ترجم", "translate"]):
            result = await translate_text(text, "المطلوب من النص")
        # Summarize
        elif any(w in lower_text for w in ["لخّص", "لخص", "summarize"]):
            result = await summarize_text(text)
        # Code request
        elif any(w in lower_text for w in ["اكتب كود", "write code", "برمج"]):
            conv = await ConversationDB.get_openai_format(user_id)
            result = await chat_with_ai(conv, text)
        # General chat
        else:
            conv = await ConversationDB.get_openai_format(user_id)
            result = await chat_with_ai(conv, text)

        # Save to memory
        await ConversationDB.add_message(user_id, "user", text)
        await ConversationDB.add_message(user_id, "assistant", result)

        # Update usage stats
        await UsageDB.increment(user_id, "messages")
        await UserDB.update(user_id, {"$inc": {"stats.total_messages": 1}})

        # Delete processing message and send result
        await processing.delete()

        # Split long messages
        if len(result) > 4000:
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await message.answer(chunk)
        else:
            await message.answer(result)

    except Exception as e:
        await processing.edit_text(f"❌ حدث خطأ غير متوقع. يرجى المحاولة مجدداً.")


@router.message(Command("stats"))
async def stats_command(message: Message):
    """Show user stats"""
    user_id = message.from_user.id
    usage = await UsageDB.get_today(user_id)
    user = await UserDB.get(user_id)

    from utils.database import SubscriptionDB
    is_pro = await SubscriptionDB.is_pro(user_id)

    await message.answer(f"""
📊 <b>إحصائياتك اليوم:</b>

💬 الرسائل: {usage.get('messages', 0)}{' / ' + str(settings.FREE_DAILY_MESSAGES) if not is_pro else ' (غير محدود)'}
🎨 الصور: {usage.get('images', 0)}{' / ' + str(settings.FREE_DAILY_IMAGES) if not is_pro else ' (غير محدود)'}
🎙️ الصوتيات: {usage.get('voice', 0)}

📈 <b>الإجمالي:</b>
💬 {user.get('stats', {}).get('total_messages', 0)} رسالة
🎨 {user.get('stats', {}).get('total_images', 0)} صورة
""")
