"""
🎙️ Voice Handler
معالج الرسائل الصوتية
"""

import io
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile

from services.ai_service import speech_to_text, text_to_speech, chat_with_ai
from utils.database import ConversationDB, UsageDB, UserDB

router = Router()


@router.message(F.voice)
async def handle_voice(message: Message):
    """Convert voice to text and reply"""
    user_id = message.from_user.id
    processing = await message.answer("🎙️ جاري تحويل الصوت إلى نص...")

    try:
        # Download voice
        file = await message.bot.get_file(message.voice.file_id)
        voice_bytes_io = await message.bot.download_file(file.file_path)
        voice_bytes = voice_bytes_io.read()

        # Transcribe
        transcript = await speech_to_text(voice_bytes, "audio.ogg")

        if transcript.startswith("❌"):
            await processing.edit_text(transcript)
            return

        await processing.edit_text(f"📝 <b>النص المستخرج:</b>\n\n<i>{transcript}</i>\n\n⏳ جاري معالجة طلبك...")

        # AI response
        conv = await ConversationDB.get_openai_format(user_id)
        ai_response = await chat_with_ai(conv, transcript)

        # Save to memory
        await ConversationDB.add_message(user_id, "user", transcript)
        await ConversationDB.add_message(user_id, "assistant", ai_response)
        await UsageDB.increment(user_id, "messages")
        await UsageDB.increment(user_id, "voice")

        await processing.delete()

        # Send text response
        await message.answer(f"🤖 <b>الرد:</b>\n\n{ai_response}")

        # Optionally send voice response
        tts_audio = await text_to_speech(ai_response[:500])
        if tts_audio:
            await message.answer_voice(
                voice=BufferedInputFile(tts_audio, filename="response.mp3"),
                caption="🔊 الرد الصوتي"
            )

    except Exception as e:
        await processing.edit_text("❌ خطأ في معالجة الصوت.")


@router.message(F.text.lower().startswith(("صوّت", "صوت", "tts", "read")))
async def text_to_speech_command(message: Message):
    """Convert text to speech"""
    text = message.text
    for prefix in ["صوّت ", "صوت ", "tts ", "read "]:
        if text.lower().startswith(prefix):
            content = text[len(prefix):].strip()
            break
    else:
        content = None

    if not content:
        await message.answer("✍️ اكتب النص بعد كلمة 'صوّت'\n\nمثال: <code>صوّت مرحباً بالعالم</code>")
        return

    processing = await message.answer("🎙️ جاري تحويل النص إلى صوت...")
    audio = await text_to_speech(content)

    if audio:
        await processing.delete()
        await message.answer_voice(
            voice=BufferedInputFile(audio, filename="speech.mp3"),
            caption=f"🔊 <i>{content[:50]}...</i>" if len(content) > 50 else f"🔊 <i>{content}</i>"
        )
    else:
        await processing.edit_text("❌ فشل في تحويل النص إلى صوت.")
