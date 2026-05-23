"""
🎨 Image Handler - Generation, editing, background removal
معالج الصور - التوليد والتعديل
"""

import io
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp

from services.ai_service import (
    smart_generate_image, remove_background,
    enhance_image, change_clothes_ai, chat_with_ai
)
from utils.database import UsageDB, UserDB, ConversationDB
from config.settings import settings

router = Router()


class ImageEditState(StatesGroup):
    waiting_for_edit_choice = State()
    waiting_for_clothes_desc = State()
    waiting_for_new_image = State()


def image_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔲 إزالة الخلفية", callback_data="img_remove_bg"),
            InlineKeyboardButton(text="✨ تحسين الجودة", callback_data="img_enhance"),
        ],
        [
            InlineKeyboardButton(text="👗 تغيير الملابس", callback_data="img_clothes"),
            InlineKeyboardButton(text="🔍 تحليل الصورة", callback_data="img_analyze"),
        ],
        [
            InlineKeyboardButton(text="❌ إلغاء", callback_data="main_menu"),
        ],
    ])


def image_style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 واقعية", callback_data="style_realistic"),
            InlineKeyboardButton(text="🎨 فنية", callback_data="style_artistic"),
        ],
        [
            InlineKeyboardButton(text="🌅 سينمائية", callback_data="style_cinematic"),
            InlineKeyboardButton(text="✏️ رسوم", callback_data="style_cartoon"),
        ],
        [
            InlineKeyboardButton(text="🚀 توليد الآن", callback_data="generate_now"),
        ],
    ])


# ============================================================
# IMAGE GENERATION
# ============================================================

@router.message(F.text.lower().startswith(("صورة", "generate image", "image:", "توليد صورة")))
async def generate_image_command(message: Message):
    """Generate image from text"""
    user_id = message.from_user.id

    # Check limit
    if not await UsageDB.can_use(user_id, "image"):
        await message.answer(
            f"⚠️ تجاوزت حد الصور اليومي ({settings.FREE_DAILY_IMAGES} صور).\n"
            "قم بالترقية لـ Pro للحصول على صور غير محدودة! 👑",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👑 ترقية للبرو", callback_data="subscription")]
            ])
        )
        return

    # Extract prompt
    text = message.text
    for prefix in ["صورة", "generate image", "image:", "توليد صورة"]:
        if text.lower().startswith(prefix):
            prompt = text[len(prefix):].strip()
            break

    if not prompt:
        await message.answer("✍️ اكتب وصف الصورة بعد كلمة 'صورة'\n\nمثال: <code>صورة جبال خضراء مع ضباب الصباح</code>")
        return

    processing = await message.answer(f"🎨 جاري توليد صورتك...\n\n<i>«{prompt[:80]}»</i>")

    try:
        result = await smart_generate_image(prompt)

        if result["type"] == "url":
            # Download and send image
            async with aiohttp.ClientSession() as session:
                async with session.get(result["data"]) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
                        await processing.delete()
                        await message.answer_photo(
                            photo=BufferedInputFile(img_bytes, filename="generated.jpg"),
                            caption=f"✨ <b>تم توليد الصورة!</b>\n\n📝 <i>{prompt[:100]}</i>\n\n🔧 المصدر: {result['source']}"
                        )
                    else:
                        await processing.edit_text("❌ فشل في تنزيل الصورة. جاري المحاولة مجدداً...")
                        # Fallback: send URL
                        await message.answer(f"🖼️ صورتك جاهزة!\n\n🔗 {result['data']}\n\n📝 {prompt[:100]}")

        # Update usage
        await UsageDB.increment(user_id, "images")
        await UserDB.update(user_id, {"$inc": {"stats.total_images": 1}})

    except Exception as e:
        await processing.edit_text(f"❌ حدث خطأ في توليد الصورة. يرجى المحاولة مجدداً.")


# ============================================================
# IMAGE EDITING - When user sends a photo
# ============================================================

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Handle received photos"""
    # Save photo file_id
    photo = message.photo[-1]  # Largest size
    await state.update_data(photo_file_id=photo.file_id)

    # Check if user sent caption
    caption = message.caption or ""

    if any(w in caption.lower() for w in ["ملابس", "clothes", "أبدّل", "تغيير"]):
        await state.set_state(ImageEditState.waiting_for_clothes_desc)
        await message.answer("👗 <b>تغيير الملابس</b>\n\nاكتب وصف الملابس الجديدة:\n\nمثال: <i>قميص أزرق فاتح مع بنطلون أسود</i>")
    elif caption:
        # Analyze with caption as question
        processing = await message.answer("🔍 جاري تحليل الصورة...")
        img_bytes = await download_file(message.bot, photo.file_id)
        if img_bytes:
            import base64
            img_b64 = base64.b64encode(img_bytes).decode()
            conv = await ConversationDB.get_openai_format(message.from_user.id)
            result = await chat_with_ai(conv, caption, image_base64=img_b64)
            await processing.delete()
            await message.answer(result)
    else:
        # Show edit options
        await message.answer(
            "🖼️ <b>استلمت صورتك!</b>\n\nماذا تريد أن أفعل بها؟",
            reply_markup=image_edit_keyboard()
        )


@router.callback_query(F.data == "img_remove_bg")
async def remove_bg_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("photo_file_id")

    if not photo_id:
        await callback.answer("❌ لم أجد الصورة، أرسلها مجدداً", show_alert=True)
        return

    await callback.message.edit_text("⏳ جاري إزالة الخلفية...")

    try:
        img_bytes = await download_file(callback.bot, photo_id)
        if img_bytes:
            result = await remove_background(img_bytes)
            if result:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=BufferedInputFile(result, filename="no_bg.png"),
                    caption="✅ تم إزالة الخلفية بنجاح!"
                )
            else:
                await callback.message.edit_text("❌ فشل في إزالة الخلفية. تأكد من إعداد Replicate API.")
    except Exception as e:
        await callback.message.edit_text("❌ حدث خطأ. يرجى المحاولة مجدداً.")
    await callback.answer()


@router.callback_query(F.data == "img_enhance")
async def enhance_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("photo_file_id")

    if not photo_id:
        await callback.answer("❌ لم أجد الصورة", show_alert=True)
        return

    await callback.message.edit_text("✨ جاري تحسين جودة الصورة (4x Upscale)...")

    try:
        img_bytes = await download_file(callback.bot, photo_id)
        if img_bytes:
            result = await enhance_image(img_bytes)
            if result:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=BufferedInputFile(result, filename="enhanced.jpg"),
                    caption="✅ تم تحسين الصورة بنجاح! (4x جودة أعلى)"
                )
            else:
                await callback.message.edit_text("❌ فشل في تحسين الصورة.")
    except Exception:
        await callback.message.edit_text("❌ حدث خطأ.")
    await callback.answer()


@router.callback_query(F.data == "img_analyze")
async def analyze_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("photo_file_id")

    await callback.message.edit_text("🔍 جاري تحليل الصورة...")

    try:
        img_bytes = await download_file(callback.bot, photo_id)
        if img_bytes:
            import base64
            img_b64 = base64.b64encode(img_bytes).decode()
            result = await chat_with_ai(
                [],
                "حلّل هذه الصورة تفصيلياً: صِف ما تراه، الألوان، العناصر، المحتوى، والأجواء العامة.",
                image_base64=img_b64
            )
            await callback.message.edit_text(f"🔍 <b>تحليل الصورة:</b>\n\n{result}")
    except Exception:
        await callback.message.edit_text("❌ حدث خطأ في تحليل الصورة.")
    await callback.answer()


@router.callback_query(F.data == "img_clothes")
async def clothes_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ImageEditState.waiting_for_clothes_desc)
    await callback.message.edit_text(
        "👗 <b>تغيير الملابس</b>\n\n"
        "اكتب وصف الملابس التي تريدها:\n\n"
        "<i>مثال: قميص أبيض رسمي مع بدلة سوداء</i>"
    )
    await callback.answer()


@router.message(ImageEditState.waiting_for_clothes_desc)
async def process_clothes_change(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get("photo_file_id")
    clothes_desc = message.text

    await state.clear()
    processing = await message.answer(f"👗 جاري تغيير الملابس إلى: <i>{clothes_desc}</i>...")

    try:
        img_bytes = await download_file(message.bot, photo_id)
        if img_bytes:
            result_url = await change_clothes_ai(img_bytes, clothes_desc)
            if result_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(result_url) as resp:
                        if resp.status == 200:
                            img_data = await resp.read()
                            await processing.delete()
                            await message.answer_photo(
                                photo=BufferedInputFile(img_data, filename="new_outfit.jpg"),
                                caption=f"✅ تم تغيير الملابس!\n\n👗 <i>{clothes_desc}</i>"
                            )
                            return
            await processing.edit_text(
                "⚠️ هذه الميزة تتطلب Replicate API مع نموذج IDM-VTON.\n"
                "تأكد من إعداد REPLICATE_API_TOKEN في الإعدادات."
            )
    except Exception as e:
        await processing.edit_text("❌ حدث خطأ في تغيير الملابس.")


# ============================================================
# UTILITY
# ============================================================

async def download_file(bot, file_id: str) -> bytes:
    """Download file from Telegram"""
    try:
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        return file_bytes.read()
    except Exception:
        return None
