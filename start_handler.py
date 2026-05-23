"""
🚀 Start & Help Handler
معالج البداية والمساعدة
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from utils.database import UserDB, SubscriptionDB, ConversationDB
from config.settings import settings

router = Router()

# ============================================================
# KEYBOARDS
# ============================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 دردشة ذكية", callback_data="feature_chat"),
            InlineKeyboardButton(text="🎨 توليد صور", callback_data="feature_image"),
        ],
        [
            InlineKeyboardButton(text="🖼️ تعديل صور", callback_data="feature_edit"),
            InlineKeyboardButton(text="🎙️ تحويل صوت", callback_data="feature_voice"),
        ],
        [
            InlineKeyboardButton(text="💻 مساعد برمجي", callback_data="feature_code"),
            InlineKeyboardButton(text="🌍 ترجمة", callback_data="feature_translate"),
        ],
        [
            InlineKeyboardButton(text="📄 تلخيص ملفات", callback_data="feature_summarize"),
            InlineKeyboardButton(text="📱 محتوى سوشيال", callback_data="feature_social"),
        ],
        [
            InlineKeyboardButton(text="👑 الاشتراك المميز", callback_data="subscription"),
            InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="settings"),
        ],
        [
            InlineKeyboardButton(text="📊 إحصائياتي", callback_data="my_stats"),
            InlineKeyboardButton(text="❓ المساعدة", callback_data="help"),
        ],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")]
    ])


# ============================================================
# HANDLERS
# ============================================================

@router.message(CommandStart())
async def start_handler(message: Message):
    """Welcome new and returning users"""
    user = await UserDB.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "مستخدم"
    )

    # Create free subscription if not exists
    await SubscriptionDB.create_free(message.from_user.id)

    is_pro = await SubscriptionDB.is_pro(message.from_user.id)
    plan_badge = "👑 Pro" if is_pro else "🆓 مجاني"

    welcome_text = f"""
✨ <b>مرحباً {message.from_user.first_name}!</b>

أنا <b>AI Bot Pro</b> — مساعدك الذكي المتكامل 🤖

{plan_badge} | الإصدار {settings.APP_VERSION}

━━━━━━━━━━━━━━━━━━━━━━━
<b>🌟 ما يمكنني فعله:</b>

🧠 <b>ذكاء اصطناعي</b> — أجيب على أي سؤال
🎨 <b>توليد صور</b> — من نص إلى صورة احترافية
🖼️ <b>تعديل صور</b> — إزالة خلفية، تحسين جودة
👗 <b>تغيير الملابس</b> — Virtual Try-On
💻 <b>برمجة</b> — كتابة وشرح وتصحيح الكود
🎙️ <b>صوت ↔ نص</b> — تحويل في الاتجاهين
🌍 <b>ترجمة</b> — جميع اللغات
📄 <b>تلخيص</b> — نصوص وملفات
📱 <b>سوشيال ميديا</b> — إنشاء محتوى
━━━━━━━━━━━━━━━━━━━━━━━

<i>اختر ما تريد أو ابدأ بكتابة رسالتك مباشرة! 👇</i>
"""

    await message.answer(welcome_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    is_pro = await SubscriptionDB.is_pro(callback.from_user.id)
    plan_badge = "👑 Pro" if is_pro else "🆓 مجاني"

    text = f"""
🏠 <b>القائمة الرئيسية</b>

{plan_badge} | مرحباً {callback.from_user.first_name}

اختر الخدمة التي تريدها:
"""
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    help_text = """
❓ <b>دليل الاستخدام</b>

━━━━━━━━━━━━━━━━━━━━━━━
<b>💬 الدردشة:</b>
• اكتب أي سؤال مباشرة
• أرسل صورة مع سؤالك لتحليلها

<b>🎨 توليد الصور:</b>
• اكتب: <code>صورة [وصف]</code>
• مثال: <code>صورة غروب شمس على الشاطئ</code>

<b>👗 تغيير الملابس:</b>
• أرسل صورتك + اكتب وصف الملابس

<b>🖼️ تعديل الصور:</b>
• أرسل الصورة + اختر العملية
• إزالة خلفية / تحسين / ضبط ألوان

<b>🎙️ الصوت:</b>
• أرسل رسالة صوتية لتحويلها لنص
• اكتب: <code>صوّت [النص]</code> لتوليد صوت

<b>💻 البرمجة:</b>
• اكتب سؤالك البرمجي مباشرة
• مثال: <code>اكتب كود Python لفرز قائمة</code>

<b>🌍 الترجمة:</b>
• اكتب: <code>ترجم [النص] إلى [اللغة]</code>

<b>📄 التلخيص:</b>
• أرسل الملف أو النص + اكتب "لخّص"
━━━━━━━━━━━━━━━━━━━━━━━

للدعم: {settings.SUPPORT_USERNAME}
"""
    await callback.message.edit_text(help_text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    from utils.database import UsageDB
    user = await UserDB.get(callback.from_user.id)
    usage = await UsageDB.get_today(callback.from_user.id)
    is_pro = await SubscriptionDB.is_pro(callback.from_user.id)

    plan = "👑 Pro" if is_pro else "🆓 مجاني"
    stats = user.get("stats", {})

    text = f"""
📊 <b>إحصائياتك</b>

👤 <b>المستخدم:</b> {callback.from_user.first_name}
🏷️ <b>الخطة:</b> {plan}

━━━━━━━━━━━━━━━━━━━━━━━
<b>📅 اليوم:</b>
💬 الرسائل: {usage.get('messages', 0)} {'/ ' + str(settings.FREE_DAILY_MESSAGES) if not is_pro else '(غير محدود)'}
🎨 الصور: {usage.get('images', 0)} {'/ ' + str(settings.FREE_DAILY_IMAGES) if not is_pro else '(غير محدود)'}
🎙️ الصوتيات: {usage.get('voice', 0)}

<b>📈 الإجمالي:</b>
💬 إجمالي الرسائل: {stats.get('total_messages', 0)}
🎨 إجمالي الصور: {stats.get('total_images', 0)}
📅 العضوية منذ: {user.get('created_at', '').strftime('%Y-%m-%d') if user.get('created_at') else 'N/A'}
━━━━━━━━━━━━━━━━━━━━━━━
"""
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("feature_"))
async def feature_info(callback: CallbackQuery):
    feature = callback.data.replace("feature_", "")

    features = {
        "chat": ("💬 الدردشة الذكية", "اكتب أي سؤال وسأجيبك بذكاء!\n\nيمكنك:\n• السؤال عن أي موضوع\n• طلب التفسير والشرح\n• طلب الآراء والأفكار\n• إرسال صورة لتحليلها"),
        "image": ("🎨 توليد الصور", "اكتب: <code>صورة [وصف تفصيلي]</code>\n\nمثال: <code>صورة مدينة مستقبلية في الليل بأضواء نيون</code>\n\n✨ مدعوم بـ DALL-E 3"),
        "edit": ("🖼️ تعديل الصور", "أرسل الصورة ثم اختر:\n• 🔲 إزالة الخلفية\n• ✨ تحسين الجودة\n• 👗 تغيير الملابس\n• 🎨 تعديل الألوان"),
        "voice": ("🎙️ تحويل الصوت", "• <b>صوت → نص:</b> أرسل رسالة صوتية\n• <b>نص → صوت:</b> اكتب <code>صوّت [النص]</code>"),
        "code": ("💻 المساعد البرمجي", "أتقن جميع لغات البرمجة:\nPython, JS, Java, C++, SQL, وغيرها\n\nيمكنني:\n• كتابة الكود\n• شرح الكود\n• تصحيح الأخطاء\n• تحسين الأداء"),
        "translate": ("🌍 الترجمة", "اكتب: <code>ترجم [النص] إلى [اللغة]</code>\n\nمثال: <code>ترجم Hello إلى العربية</code>\n\nأدعم 100+ لغة!"),
        "summarize": ("📄 تلخيص الملفات", "أرسل:\n• ملف نصي\n• PDF\n• نص طويل\n\nثم اكتب 'لخّص' وسأقدم ملخصاً احترافياً"),
        "social": ("📱 محتوى السوشيال ميديا", "اكتب ما تحتاج:\n• بوست إنستغرام/تويتر\n• هاشتاقات\n• كابشن صور\n• خطة محتوى\n• سكريبت فيديو"),
    }

    title, desc = features.get(feature, ("❓", "ميزة غير معروفة"))
    text = f"<b>{title}</b>\n\n{desc}\n\n<i>ابدأ الآن! 👇</i>"
    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()


@router.message(Command("clear"))
async def clear_history(message: Message):
    """Clear conversation history"""
    await ConversationDB.clear_history(message.from_user.id)
    await message.answer("🗑️ تم مسح سجل المحادثة بنجاح!\nيمكنك البدء من جديد 🆕")


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("""
❓ <b>الأوامر المتاحة:</b>

/start — بدء البوت / القائمة الرئيسية
/clear — مسح سجل المحادثة
/stats — إحصائياتك
/plan — معلومات الاشتراك
/help — هذه المساعدة

<b>أو اكتب مباشرة:</b>
• صورة [وصف] — لتوليد صورة
• ترجم [نص] إلى [لغة] — للترجمة
• لخّص [نص] — للتلخيص
• صوّت [نص] — لتوليد صوت
""")
