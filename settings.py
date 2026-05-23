"""
⚙️ Bot Configuration Settings
إعدادات البوت الكاملة
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # ===== TELEGRAM =====
    TELEGRAM_TOKEN: str = "8728825707:AAHe4Kr-dkCHSYhkfCyOmq0sdm0ZsDQecFs"
    BOT_USERNAME: str = "Star_Ton_sell_Bot"
    ADMIN_IDS: List[int] = [6721652980]  # Add your Telegram ID

    # ===== AI APIs =====
    OPENAI_API_KEY: str = "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."
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"

    REPLICATE_API_TOKEN: str = "r8_2xj84ddDY2gzR8TEYsZaeQ6KMYVNcSZ1gJlP8"
    STABILITY_API_KEY: str = "sk-BObQCHYUkGmntQd1Xs1cu3QzoP2dUVFdSIfG9W3FOqermrVp"
    ANTHROPIC_API_KEY: str = ""  # Optional

    # Pollinations (Free - no key needed)
    POLLINATIONS_BASE_URL: str = "https://image.pollinations.ai/prompt"

    # ===== DATABASE =====
    MONGODB_URL: str = "mongodb+srv://hussensami9494_db_user:N72GursPdSIyWffp@cluster0.diq9r1d.mongodb.net/?appName=Cluster0"
    DB_NAME: str = "ai_telegram_bot"

    # OR PostgreSQL
    POSTGRES_URL: Optional[str] = None

    # ===== REDIS =====
    REDIS_URL: str = "redis://localhost:6379"

    # ===== SUBSCRIPTION PLANS =====
    FREE_DAILY_MESSAGES: int = 20
    FREE_DAILY_IMAGES: int = 3
    PRO_MONTHLY_PRICE: float = 9.99
    PRO_YEARLY_PRICE: float = 79.99

    # Payment
    STRIPE_SECRET_KEY: Optional[str] = None
    PAYMENT_PROVIDER_TOKEN: Optional[str] = None  # Telegram Payments

    # ===== FEATURES =====
    MAX_FILE_SIZE_MB: int = 20
    MAX_VOICE_DURATION_SEC: int = 300
    MAX_CONTEXT_MESSAGES: int = 20
    SPAM_COOLDOWN_SEC: int = 2
    MAX_REQUESTS_PER_MIN: int = 15

    # ===== APP =====
    APP_NAME: str = "🤖 AI Bot Pro"
    APP_VERSION: str = "2.0.0"
    SUPPORT_USERNAME: str = "@L_P_50"
    CHANNEL_USERNAME: str = "@L_P_50"
    WEBHOOK_URL: Optional[str] = None  # For production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
