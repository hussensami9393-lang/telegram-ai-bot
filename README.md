# 🤖 AI Telegram Bot Pro - دليل الإعداد الكامل

## نظرة عامة
بوت Telegram متكامل بالذكاء الاصطناعي مع أكثر من 15 ميزة متقدمة.

---

## 📋 المتطلبات

- Python 3.11+
- MongoDB (Atlas مجاني أو محلي)
- Redis (اختياري - للتخزين المؤقت)
- حسابات API (انظر الخطوات أدناه)

---

## 🚀 خطوات الإعداد

### 1. إنشاء البوت على Telegram

1. افتح [@BotFather](https://t.me/BotFather) على Telegram
2. أرسل `/newbot`
3. اختر اسماً للبوت
4. احفظ الـ **TOKEN** الذي ستحصل عليه

### 2. الحصول على مفاتيح API

#### OpenAI (مطلوب - للدردشة وتوليد الصور والصوت)
1. سجّل على [platform.openai.com](https://platform.openai.com)
2. اذهب إلى API Keys
3. أنشئ مفتاح جديد
4. ⚠️ تأكد من وضع رصيد في الحساب

#### Replicate (لتعديل الصور وإزالة الخلفية)
1. سجّل على [replicate.com](https://replicate.com)
2. اذهب إلى Account > API Tokens
3. أنشئ token جديد

#### MongoDB Atlas (مجاني - لقاعدة البيانات)
1. سجّل على [mongodb.com/atlas](https://cloud.mongodb.com)
2. أنشئ Cluster مجاني (M0)
3. أنشئ مستخدم قاعدة بيانات
4. احصل على Connection String

### 3. إعداد ملف .env

```bash
cp .env.example .env
nano .env  # عدّل القيم
```

المتغيرات المطلوبة كحد أدنى:
```
TELEGRAM_TOKEN=...
OPENAI_API_KEY=...
MONGODB_URL=...
ADMIN_IDS=[your_telegram_id]
```

### 4. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 5. تشغيل البوت محلياً

```bash
cd bot
python main.py
```

---

## ☁️ النشر على Fly.io (24/7 مجاني)

### 1. تثبيت Fly CLI

```bash
# Windows
iwr https://fly.io/install.ps1 -useb | iex

# Linux/Mac
curl -L https://fly.io/install.sh | sh
```

### 2. تسجيل الدخول

```bash
fly auth login
```

### 3. إنشاء التطبيق

```bash
fly apps create ai-telegram-bot
```

### 4. إعداد متغيرات البيئة

```bash
fly secrets set TELEGRAM_TOKEN="your_token"
fly secrets set OPENAI_API_KEY="sk-..."
fly secrets set MONGODB_URL="mongodb+srv://..."
fly secrets set ADMIN_IDS="[123456789]"
fly secrets set REPLICATE_API_TOKEN="r8_..."
```

### 5. النشر

```bash
fly deploy
```

### 6. مراقبة السجلات

```bash
fly logs
```

---

## 🎯 الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| `/start` | بدء البوت وعرض القائمة |
| `/clear` | مسح سجل المحادثة |
| `/stats` | إحصائياتك |
| `/plan` | معلومات الاشتراك |
| `/help` | دليل الاستخدام |
| `/admin` | لوحة الأدمن (للمشرفين) |

### أوامر نصية مباشرة:
- `صورة [وصف]` — توليد صورة
- `ترجم [نص] إلى [لغة]` — ترجمة
- `لخّص [نص]` — تلخيص
- `صوّت [نص]` — تحويل نص لصوت

---

## 🖼️ ميزات تعديل الصور

1. **إرسال الصورة** ← البوت يعرض خيارات:
   - 🔲 إزالة الخلفية
   - ✨ تحسين الجودة (4x)
   - 👗 تغيير الملابس
   - 🔍 تحليل الصورة

2. **إرسال الصورة مع caption** ← يحلل الصورة مع سؤالك

---

## 💰 نظام الاشتراكات

| الخطة | الرسائل | الصور | الميزات |
|-------|---------|-------|---------|
| مجاني | 20/يوم | 3/يوم | أساسية |
| Pro شهري | غير محدود | غير محدود | كل الميزات |
| Pro سنوي | غير محدود | غير محدود | كل الميزات + خصم |

### منح Pro يدوياً (للأدمن):
1. `/admin` ← 👑 منح Pro
2. أدخل ID المستخدم
3. أدخل عدد الأشهر

---

## 🛡️ الحماية المدمجة

- **Anti-Spam**: حد أقصى 15 رسالة/دقيقة
- **Cooldown**: ثانيتان بين كل رسالة
- **Auth**: فحص الحظر لكل رسالة
- **Rate Limiting**: حدود يومية للخطة المجانية
- **File Size Limit**: 20MB للملفات

---

## 🔧 إضافة APIs جديدة

كل الخدمات في `services/ai_service.py`. لإضافة خدمة جديدة:

```python
async def my_new_service(input_data: str) -> str:
    """وصف الخدمة"""
    # كودك هنا
    pass
```

ثم استدعِها من الـ handler المناسب.

---

## 📊 هيكل المشروع

```
telegram-ai-bot/
├── bot/
│   └── main.py              # نقطة البداية
├── config/
│   └── settings.py          # جميع الإعدادات
├── handlers/
│   ├── start_handler.py     # البداية والقوائم
│   ├── chat_handler.py      # الدردشة الذكية
│   ├── image_handler.py     # الصور
│   ├── voice_handler.py     # الصوت
│   ├── file_handler.py      # الملفات
│   ├── subscription_handler.py  # الاشتراكات
│   └── admin_handler.py     # لوحة الأدمن
├── services/
│   └── ai_service.py        # جميع خدمات AI
├── middlewares/
│   ├── anti_spam.py         # مكافحة السبام
│   ├── auth.py              # المصادقة
│   └── logging_middleware.py # التسجيل
├── utils/
│   └── database.py          # قاعدة البيانات
├── requirements.txt
├── .env.example
├── Dockerfile
└── fly.toml
```

---

## 📞 الدعم والتطوير

للدعم التقني أو إضافة ميزات جديدة، تواصل مع فريق التطوير.

**نصيحة**: للنشر المجاني على Fly.io، يكفي الحساب المجاني (3 VMs مجانية).
