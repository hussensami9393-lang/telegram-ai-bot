"""
👑 Admin Handler - Full Admin Panel
لوحة تحكم المشرف الكاملة
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from utils.database import UserDB, SubscriptionDB, UsageDB, get_db
from config.settings import settings

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 المستخدمون", callback_data="admin_users"),
            InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="📢 رسالة جماعية", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="👑 منح Pro", callback_data="admin_grant_pro"),
        ],
        [
            InlineKeyboardButton(text="🚫 حظر مستخدم", callback_data="admin_ban"),
            InlineKeyboardButton(text="✅ رفع الحظر", callback_data="admin_unban"),
        ],
        [
            InlineKeyboardButton(text="🔄 إعادة تشغيل", callback_data="admin_restart"),
        ],
    ])


class AdminState(StatesGroup):
    broadcast_message = State()
    grant_pro_user_id = State()
    grant_pro_months = State()
    ban_user_id = State()
    ban_reason = State()
    unban_user_id = State()


# ============================================================
# ADMIN PANEL
# ============================================================

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    db = get_db()
    total_users = await UserDB.count()
    today_str = datetime.utcnow().date().isoformat()
    new_today = await db.users.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
    })
    pro_count = await db.subscriptions.count_documents({"plan": {"$ne": "free"}})

    text = f"""
👑 <b>لوحة تحكم الأدمن</b>

━━━━━━━━━━━━━━━━━━━━━━━
👥 إجمالي المستخدمين: <b>{total_users}</b>
🆕 جدد اليوم: <b>{new_today}</b>
💎 مشتركو Pro: <b>{pro_count}</b>
🤖 البوت: <b>يعمل ✅</b>
━━━━━━━━━━━━━━━━━━━━━━━
"""
    await message.answer(text, reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ غير مصرح", show_alert=True)
        return

    db = get_db()
    total_users = await UserDB.count()
    pro_count = await db.subscriptions.count_documents({"plan": {"$ne": "free"}})
    total_messages = await db.messages.count_documents({})
    banned_count = await db.users.count_documents({"is_banned": True})
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_users = await db.users.count_documents({"created_at": {"$gte": today_start}})

    text = f"""
📊 <b>إحصائيات البوت الكاملة</b>

👥 <b>المستخدمون:</b>
• الإجمالي: {total_users}
• جدد اليوم: {today_users}
• محظورون: {banned_count}

💎 <b>الاشتراكات:</b>
• Pro: {pro_count}
• مجاني: {total_users - pro_count}
• نسبة التحويل: {(pro_count/total_users*100):.1f}% 

💬 <b>النشاط:</b>
• إجمالي الرسائل: {total_messages}
• متوسط/مستخدم: {total_messages//max(total_users,1)}
"""
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    users = await UserDB.get_all(limit=10)
    text = "👥 <b>آخر المستخدمين:</b>\n\n"

    for user in users:
        pro = "👑" if user.get("subscription", {}).get("plan") == "pro" else "🆓"
        banned = "🚫" if user.get("is_banned") else ""
        text += f"{pro} {banned} <b>{user.get('first_name', 'N/A')}</b> | ID: <code>{user['user_id']}</code>\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_back")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.broadcast_message)
    await callback.message.edit_text(
        "📢 <b>رسالة جماعية</b>\n\nاكتب الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n<i>أو أرسل /cancel للإلغاء</i>"
    )
    await callback.answer()


@router.message(AdminState.broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    users = await UserDB.get_all(limit=10000)
    success = 0
    failed = 0

    progress = await message.answer(f"📢 جاري الإرسال... 0/{len(users)}")

    for i, user in enumerate(users):
        try:
            await message.bot.send_message(
                user["user_id"],
                f"📢 <b>إعلان من البوت:</b>\n\n{message.text}"
            )
            success += 1
        except Exception:
            failed += 1

        if (i + 1) % 50 == 0:
            await progress.edit_text(f"📢 جاري الإرسال... {i+1}/{len(users)}")

    await progress.edit_text(
        f"✅ <b>تم الإرسال!</b>\n\n✅ نجح: {success}\n❌ فشل: {failed}"
    )


@router.callback_query(F.data == "admin_grant_pro")
async def admin_grant_pro_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.grant_pro_user_id)
    await callback.message.edit_text("👑 أدخل ID المستخدم لمنحه Pro:")
    await callback.answer()


@router.message(AdminState.grant_pro_user_id)
async def admin_grant_pro_months(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(target_user_id=user_id)
        await state.set_state(AdminState.grant_pro_months)
        await message.answer("📅 كم شهراً تريد منحه? (1-12)")
    except ValueError:
        await message.answer("❌ ID غير صالح")


@router.message(AdminState.grant_pro_months)
async def admin_grant_pro_confirm(message: Message, state: FSMContext):
    try:
        months = int(message.text)
        data = await state.get_data()
        user_id = data["target_user_id"]
        await state.clear()

        await SubscriptionDB.upgrade(user_id, "pro", months)
        await message.answer(f"✅ تم منح Pro لـ {user_id} لمدة {months} شهر(أشهر)")

        try:
            await message.bot.send_message(
                user_id,
                f"🎉 تهانينا! تم تفعيل اشتراك <b>Pro</b> لحسابك لمدة <b>{months} شهر</b>!\n\nاستمتع بجميع المميزات! 🚀"
            )
        except Exception:
            pass
    except ValueError:
        await state.clear()
        await message.answer("❌ رقم غير صالح")


@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.ban_user_id)
    await callback.message.edit_text("🚫 أدخل ID المستخدم لحظره:")
    await callback.answer()


@router.message(AdminState.ban_user_id)
async def admin_ban_confirm(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await UserDB.ban(user_id, "تم الحظر من الأدمن")
        await state.clear()
        await message.answer(f"✅ تم حظر المستخدم {user_id}")
    except Exception:
        await state.clear()
        await message.answer("❌ خطأ في الحظر")


@router.callback_query(F.data == "admin_unban")
async def admin_unban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminState.unban_user_id)
    await callback.message.edit_text("✅ أدخل ID المستخدم لرفع الحظر:")
    await callback.answer()


@router.message(AdminState.unban_user_id)
async def admin_unban_confirm(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await UserDB.unban(user_id)
        await state.clear()
        await message.answer(f"✅ تم رفع الحظر عن {user_id}")
    except Exception:
        await state.clear()
        await message.answer("❌ خطأ")


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    db = get_db()
    total_users = await UserDB.count()
    text = f"👑 <b>لوحة تحكم الأدمن</b>\n\n👥 المستخدمون: <b>{total_users}</b>"
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()
