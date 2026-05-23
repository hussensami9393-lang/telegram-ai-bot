"""
🗄️ Database Models & Initialization
نماذج قاعدة البيانات
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio

from config.settings import settings

# Global DB client
client: Optional[AsyncIOMotorClient] = None
db = None


async def init_db():
    """Initialize database connection"""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DB_NAME]

    # Create indexes
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("username")
    await db.messages.create_index("user_id")
    await db.messages.create_index("created_at")
    await db.subscriptions.create_index("user_id", unique=True)
    await db.usage.create_index([("user_id", 1), ("date", 1)])

    return db


def get_db():
    return db


# ============================================================
# USER MODEL
# ============================================================

class UserDB:
    collection_name = "users"

    @staticmethod
    async def get(user_id: int) -> Optional[Dict]:
        return await db.users.find_one({"user_id": user_id})

    @staticmethod
    async def create(user_id: int, username: str, first_name: str,
                     language: str = "ar") -> Dict:
        user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "language": language,
            "is_banned": False,
            "is_admin": user_id in settings.ADMIN_IDS,
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "preferences": {
                "ai_model": "gpt-4o",
                "language": language,
                "image_style": "realistic",
                "voice_enabled": True,
            },
            "stats": {
                "total_messages": 0,
                "total_images": 0,
                "total_voice": 0,
            }
        }
        await db.users.insert_one(user)
        return user

    @staticmethod
    async def update(user_id: int, data: Dict):
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {**data, "last_seen": datetime.utcnow()}}
        )

    @staticmethod
    async def get_or_create(user_id: int, username: str, first_name: str) -> Dict:
        user = await UserDB.get(user_id)
        if not user:
            user = await UserDB.create(user_id, username, first_name)
        else:
            await UserDB.update(user_id, {"last_seen": datetime.utcnow()})
        return user

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 50) -> List[Dict]:
        cursor = db.users.find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    @staticmethod
    async def count() -> int:
        return await db.users.count_documents({})

    @staticmethod
    async def ban(user_id: int, reason: str = ""):
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": True, "ban_reason": reason}}
        )

    @staticmethod
    async def unban(user_id: int):
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": False, "ban_reason": ""}}
        )


# ============================================================
# CONVERSATION / MEMORY MODEL
# ============================================================

class ConversationDB:

    @staticmethod
    async def get_history(user_id: int, limit: int = 20) -> List[Dict]:
        cursor = db.messages.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        return list(reversed(messages))

    @staticmethod
    async def add_message(user_id: int, role: str, content: str,
                          msg_type: str = "text"):
        await db.messages.insert_one({
            "user_id": user_id,
            "role": role,
            "content": content,
            "type": msg_type,
            "created_at": datetime.utcnow()
        })

    @staticmethod
    async def clear_history(user_id: int):
        await db.messages.delete_many({"user_id": user_id})

    @staticmethod
    async def get_openai_format(user_id: int) -> List[Dict]:
        """Get conversation in OpenAI format"""
        history = await ConversationDB.get_history(user_id, limit=settings.MAX_CONTEXT_MESSAGES)
        return [{"role": msg["role"], "content": msg["content"]} for msg in history]


# ============================================================
# SUBSCRIPTION MODEL
# ============================================================

class SubscriptionDB:

    @staticmethod
    async def get(user_id: int) -> Optional[Dict]:
        return await db.subscriptions.find_one({"user_id": user_id})

    @staticmethod
    async def create_free(user_id: int):
        existing = await SubscriptionDB.get(user_id)
        if not existing:
            await db.subscriptions.insert_one({
                "user_id": user_id,
                "plan": "free",
                "started_at": datetime.utcnow(),
                "expires_at": None,
                "is_active": True,
            })

    @staticmethod
    async def upgrade(user_id: int, plan: str, months: int = 1):
        expires = datetime.utcnow() + timedelta(days=30 * months)
        await db.subscriptions.update_one(
            {"user_id": user_id},
            {"$set": {
                "plan": plan,
                "started_at": datetime.utcnow(),
                "expires_at": expires,
                "is_active": True,
            }},
            upsert=True
        )

    @staticmethod
    async def is_pro(user_id: int) -> bool:
        # Admins always have Pro
        if user_id in settings.ADMIN_IDS:
            return True
        sub = await SubscriptionDB.get(user_id)
        if not sub:
            return False
        if sub["plan"] == "free":
            return False
        if sub.get("expires_at") and sub["expires_at"] < datetime.utcnow():
            await db.subscriptions.update_one(
                {"user_id": user_id}, {"$set": {"plan": "free", "is_active": True}}
            )
            return False
        return True


# ============================================================
# USAGE TRACKING
# ============================================================

class UsageDB:

    @staticmethod
    async def get_today(user_id: int) -> Dict:
        today = datetime.utcnow().date().isoformat()
        usage = await db.usage.find_one({"user_id": user_id, "date": today})
        if not usage:
            return {"messages": 0, "images": 0, "voice": 0}
        return usage

    @staticmethod
    async def increment(user_id: int, field: str):
        today = datetime.utcnow().date().isoformat()
        await db.usage.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {field: 1}},
            upsert=True
        )

    @staticmethod
    async def can_use(user_id: int, feature: str) -> bool:
        """Check if user can use a feature based on their plan"""
        if user_id in settings.ADMIN_IDS:
            return True
        is_pro = await SubscriptionDB.is_pro(user_id)
        if is_pro:
            return True

        usage = await UsageDB.get_today(user_id)
        if feature == "message" and usage.get("messages", 0) >= settings.FREE_DAILY_MESSAGES:
            return False
        if feature == "image" and usage.get("images", 0) >= settings.FREE_DAILY_IMAGES:
            return False
        return True
