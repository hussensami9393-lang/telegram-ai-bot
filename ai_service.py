"""
🧠 AI Services - All AI integrations
خدمات الذكاء الاصطناعي المتكاملة
"""

import aiohttp
import base64
import asyncio
import openai
from typing import Optional, List, Dict
from openai import AsyncOpenAI

from config.settings import settings

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """أنت مساعد ذكاء اصطناعي متقدم ومتعدد المهام، تتحدث العربية والإنجليزية بطلاقة.

قدراتك تشمل:
• الإجابة على أي سؤال بدقة واحترافية
• كتابة وشرح وتصحيح الأكواد بجميع لغات البرمجة
• ترجمة النصوص بين جميع اللغات
• تلخيص النصوص والوثائق
• إنشاء محتوى إبداعي للسوشيال ميديا
• تقديم أفكار ومشاريع ومواقع
• تحليل الصور والملفات
• حل المسائل الرياضية والعلمية

أسلوبك: ذكي، ودود، واحترافي. ردودك منظمة وواضحة. استخدم الإيموجي المناسبة لجعل الردود أكثر جاذبية.
تذكر دائماً: كن موجزاً عند الحاجة ومفصلاً عند الطلب."""


# ============================================================
# CHAT AI
# ============================================================

async def chat_with_ai(
    messages: List[Dict],
    user_message: str,
    image_base64: Optional[str] = None,
    model: str = None
) -> str:
    """Send message to OpenAI and get response"""
    try:
        model = model or settings.OPENAI_MODEL

        # Build message content
        if image_base64:
            content = [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "high"
                    }
                }
            ]
        else:
            content = user_message

        # Prepare full conversation
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
            {"role": "user", "content": content}
        ]

        response = await openai_client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=2048,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except openai.RateLimitError:
        return "⚠️ عذراً، تم تجاوز حد الطلبات. يرجى المحاولة بعد لحظات."
    except openai.AuthenticationError:
        return "❌ خطأ في مفتاح API. يرجى التواصل مع الدعم."
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)[:100]}"


# ============================================================
# IMAGE GENERATION
# ============================================================

async def generate_image_dalle(prompt: str, size: str = "1024x1024") -> Optional[str]:
    """Generate image using DALL-E 3"""
    try:
        # Enhance prompt
        enhanced = f"High quality, detailed, professional: {prompt}"

        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return None


async def generate_image_pollinations(prompt: str, width: int = 1024,
                                       height: int = 1024) -> str:
    """Generate image using Pollinations (FREE, no key needed)"""
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    seed = asyncio.get_event_loop().time().__hash__() % 100000
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    return url


async def generate_image_stability(prompt: str) -> Optional[bytes]:
    """Generate image using Stability AI"""
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {settings.STABILITY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_data = data["artifacts"][0]["base64"]
                    return base64.b64decode(img_data)
        return None
    except Exception:
        return None


async def smart_generate_image(prompt: str) -> Dict:
    """Smart image generation with fallback"""
    # Try DALL-E first
    url = await generate_image_dalle(prompt)
    if url:
        return {"type": "url", "data": url, "source": "DALL-E 3"}

    # Fallback to Pollinations (free)
    url = generate_image_pollinations(prompt)
    return {"type": "url", "data": await url, "source": "Pollinations AI"}


# ============================================================
# IMAGE EDITING
# ============================================================

async def remove_background(image_bytes: bytes) -> Optional[bytes]:
    """Remove background using Replicate"""
    try:
        import replicate
        import io

        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        output = await asyncio.to_thread(
            client.run,
            "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec05c17",
            input={"image": image_bytes}
        )
        if output:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(output)) as resp:
                    if resp.status == 200:
                        return await resp.read()
        return None
    except Exception as e:
        return None


async def enhance_image(image_bytes: bytes) -> Optional[bytes]:
    """Enhance/upscale image using Replicate"""
    try:
        import replicate
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        output = await asyncio.to_thread(
            client.run,
            "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
            input={"image": image_bytes, "scale": 4}
        )
        if output:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(output)) as resp:
                    if resp.status == 200:
                        return await resp.read()
        return None
    except Exception:
        return None


async def change_clothes_ai(person_image: bytes, clothes_description: str) -> Optional[str]:
    """Virtual try-on using Replicate"""
    try:
        import replicate
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

        # Use IDM-VTON or similar model
        output = await asyncio.to_thread(
            client.run,
            "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
            input={
                "human_img": person_image,
                "garment_des": clothes_description,
            }
        )
        if output:
            return str(output)
        return None
    except Exception as e:
        return None


# ============================================================
# VOICE / SPEECH
# ============================================================

async def speech_to_text(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """Convert voice to text using Whisper"""
    try:
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        return transcript
    except Exception as e:
        return f"❌ خطأ في تحويل الصوت: {str(e)[:100]}"


async def text_to_speech(text: str, voice: str = "nova") -> Optional[bytes]:
    """Convert text to speech using OpenAI TTS"""
    try:
        response = await openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,  # alloy, echo, fable, onyx, nova, shimmer
            input=text[:4000],  # Max 4096 chars
        )
        return response.content
    except Exception:
        return None


# ============================================================
# TEXT UTILITIES
# ============================================================

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language"""
    prompt = f"ترجم النص التالي إلى {target_lang}. أعطِ الترجمة فقط بدون أي شرح:\n\n{text}"
    result = await chat_with_ai([], prompt)
    return result


async def summarize_text(text: str) -> str:
    """Summarize text"""
    prompt = f"""لخّص النص التالي بشكل احترافي:
- استخدم نقاط رئيسية
- اجعله موجزاً ومفيداً  
- حافظ على المعلومات المهمة

النص:
{text[:8000]}"""
    return await chat_with_ai([], prompt)


async def analyze_file_content(content: str, filename: str) -> str:
    """Analyze uploaded file content"""
    prompt = f"""حلّل محتوى الملف "{filename}" وقدّم:
1. ملخصاً شاملاً
2. النقاط الرئيسية
3. أي معلومات مهمة

محتوى الملف:
{content[:6000]}"""
    return await chat_with_ai([], prompt)
