"""
💳 Subscription Handler
نظام الاشتراكات
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime

from utils.database import SubscriptionDB
from config.settings import settings

router = Router()


def subscription_keyboard(is_pro: bool) -> InlineKeyboardMarkup:
    if is_pro:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")]
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"💎 شهري - ${settings.PRO_MONTHLY_PRICE}",
                callback_data="pay_monthly"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"👑 سنوي - ${settings.PRO_YEARLY_PRICE} (وفّر 33%)",
                callback_data="pay_yearly"
            ),
        ],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")],
    ])


@router.callback_query(F.data == "subscription")
async def subscription_info(callback: CallbackQuery):
    is_pro = await SubscriptionDB.is_pro(callback.from_user.id)
    sub = await SubscriptionDB.get(callback.from_user.id)

    if is_pro:
        expires = sub.get("expires_at")
        expires_str = expires.strftime("%Y-%m-%d") if expires else "غير محدود"
        text = f"""
👑 <b>أنت مشترك في Pro!</b>

✅ رسائل غير محدودة
✅ صور غير محدودة  
✅ جميع الميزات متاحة
✅ أولوية في الاستجابة
✅ نماذج AI متقدمة

📅 الاشتراك حتى: <b>{expires_str}</b>

شكراً لدعمك! 🙏
"""
    else:
        text = f"""
💎 <b>ترقية إلى Pro</b>

<b>المجاني (حالياً):</b>
✅ {settings.FREE_DAILY_MESSAGES} رسائل يومياً
✅ {settings.FREE_DAILY_IMAGES} صور يومياً
❌ ميزات محدودة

━━━━━━━━━━━━━━━━━━━━━━━

<b>Pro - ما ستحصل عليه:</b>
🚀 رسائل وصور <b>غير محدودة</b>
🧠 GPT-4o (النموذج الأقوى)
🎨 DALL-E 3 بجودة عالية
👗 تغيير الملابس AI
✨ تحسين الصور - جودة 4x
🎙️ صوت غير محدود
📁 معالجة ملفات متقدمة
⚡ استجابة سريعة جداً
🌍 جميع اللغات
🔒 خصوصية كاملة

━━━━━━━━━━━━━━━━━━━━━━━

💎 شهري: <b>${settings.PRO_MONTHLY_PRICE}</b>/شهر
👑 سنوي: <b>${settings.PRO_YEARLY_PRICE}</b>/سنة <i>(وفّر 33%)</i>
"""

    await callback.message.edit_text(
        text,
        reply_markup=subscription_keyboard(is_pro)
    )
    await callback.answer()


@router.callback_query(F.data.in_(["pay_monthly", "pay_yearly"]))
async def process_payment(callback: CallbackQuery):
    plan = "شهري" if callback.data == "pay_monthly" else "سنوي"
    price = settings.PRO_MONTHLY_PRICE if callback.data == "pay_monthly" else settings.PRO_YEARLY_PRICE

    # If Telegram Payments configured
    if settings.PAYMENT_PROVIDER_TOKEN:
        await callback.message.answer_invoice(
            title=f"AI Bot Pro - {plan}",
            description="اشتراك AI Bot Pro - ذكاء اصطناعي غير محدود",
            payload=f"pro_{callback.data.replace('pay_', '')}",
            provider_token=settings.PAYMENT_PROVIDER_TOKEN,
            currency="USD",
            prices=[{"label": f"AI Bot Pro {plan}", "amount": int(price * 100)}],
        )
    else:
        # Show payment instructions
        await callback.message.edit_text(f"""
💳 <b>الدفع - Pro {plan}</b>

المبلغ: <b>${price}</b>

للاشتراك، تواصل مع:
{settings.SUPPORT_USERNAME}

أرسل: "اشتراك Pro {plan}" 
وسنفعّل حسابك خلال دقائق ✅

━━━━━━━━━━━━━━━━━━━━━━━
🔒 طرق الدفع: USDT, PayPal, بطاقة ائتمان
""",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 تواصل للدفع", url=f"https://t.me/{settings.SUPPORT_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton(text="🔙 رجوع", callback_data="subscription")],
            ])
        )
    await callback.answer()


@router.message(Command("plan"))
async def plan_command(message: Message):
    is_pro = await SubscriptionDB.is_pro(message.from_user.id)
    sub = await SubscriptionDB.get(message.from_user.id)
    plan = sub.get("plan", "free") if sub else "free"

    await message.answer(
        f"💎 خطتك الحالية: <b>{'👑 Pro' if is_pro else '🆓 مجاني'}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 إدارة الاشتراك", callback_data="subscription")]
        ])
    )
