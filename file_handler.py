"""
📄 File Handler - Process uploaded documents
معالج الملفات
"""

from aiogram import Router, F
from aiogram.types import Message

from services.ai_service import analyze_file_content, summarize_text

router = Router()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.message(F.document)
async def handle_document(message: Message):
    """Handle uploaded documents"""
    doc = message.document

    if doc.file_size > MAX_FILE_SIZE:
        await message.answer("❌ حجم الملف كبير جداً (الحد الأقصى 20MB)")
        return

    processing = await message.answer(f"📄 جاري قراءة الملف: <b>{doc.file_name}</b>...")

    try:
        # Download file
        file = await message.bot.get_file(doc.file_id)
        file_bytes_io = await message.bot.download_file(file.file_path)
        content_bytes = file_bytes_io.read()

        # Try to decode as text
        content = None
        for encoding in ['utf-8', 'arabic', 'latin-1', 'cp1256']:
            try:
                content = content_bytes.decode(encoding)
                break
            except Exception:
                continue

        if not content:
            await processing.edit_text("❌ لا يمكن قراءة هذا النوع من الملفات. يدعم البوت الملفات النصية حالياً.")
            return

        # Check user's caption/request
        user_request = message.caption or "لخّص هذا الملف"

        await processing.edit_text("🧠 جاري تحليل المحتوى...")

        result = await analyze_file_content(content, doc.file_name)

        await processing.delete()
        await message.answer(f"📋 <b>تحليل: {doc.file_name}</b>\n\n{result}")

    except Exception as e:
        await processing.edit_text("❌ حدث خطأ في معالجة الملف.")
