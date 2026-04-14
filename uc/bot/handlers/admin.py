"""
Admin handlerlari - Bot boshqaruvi
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_admin_menu, get_order_actions
from data.database import db
from data.models import OrderStatus, User
from data.config import bot_config

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    """Admin tekshiruvi"""
    return user_id in bot_config.ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizga ruxsat yo'q!")
        return
    
    stats = await get_detailed_stats()
    
    await message.answer(
        f"🔧 <b>Admin Panel</b>\n\n"
        f"📊 <b>Bugungi statistika:</b>\n"
        f"• Buyurtmalar: {stats['today_orders']}\n"
        f"• Daromad: {stats['today_revenue']:,} so'm\n"
        f"• Yangi foydalanuvchilar: {stats['new_users']}\n\n"
        f"⏳ <b>Kutilayotgan:</b> {stats['pending_orders']} ta\n"
        f"❌ <b>Xatoliklar:</b> {stats['failed_orders']} ta",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

async def get_detailed_stats():
    """Batafsil statistika"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    
    # Bugun
    today_stats = await db.get_stats("today")
    
    # Xatoliklar
    from data.models import Order
    from sqlalchemy import select, func
    from data.database import db as database
    
    async with database.async_session() as session:
        failed_result = await session.execute(
            select(func.count(Order.id)).where(
                Order.status == OrderStatus.FAILED,
                Order.created_at >= today
            )
        )
        failed = failed_result.scalar()
    
    return {
        **today_stats,
        "failed_orders": failed
    }

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Batafsil statistika"""
    if not is_admin(callback.from_user.id):
        return
    
    # Oxirgi 7 kun statistikasi
    stats_7d = await db.get_stats("week")
    stats_30d = await db.get_stats("month")
    
    await callback.message.edit_text(
        f"📊 <b>To'liq statistika:</b>\n\n"
        f"<b>Bugun:</b>\n"
        f"• Buyurtmalar: {stats_7d['total_orders']}\n"
        f"• Daromad: {stats_7d['total_revenue']:,} so'm\n\n"
        f"<b>So'nggi 7 kun:</b>\n"
        f"• Buyurtmalar: {stats_7d['total_orders']}\n"
        f"• Daromad: {stats_7d['total_revenue']:,} so'm\n\n"
        f"<b>So'nggi 30 kun:</b>\n"
        f"• Buyurtmalar: {stats_30d['total_orders']}\n"
        f"• Daromad: {stats_30d['total_revenue']:,} so'm",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_orders")
async def show_orders(callback: CallbackQuery):
    """Buyurtmalarni ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    from data.models import Order
    from sqlalchemy import select, desc
    from data.database import db as database
    
    async with database.async_session() as session:
        result = await session.execute(
            select(Order).order_by(desc(Order.created_at)).limit(10)
        )
        orders = result.scalars().all()
    
    if not orders:
        await callback.answer("Buyurtmalar yo'q!")
        return
    
    text = "📦 <b>So'nggi 10 buyurtma:</b>\n\n"
    for order in orders:
        status_emoji = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.PAYMENT_PENDING: "💳",
            OrderStatus.PAYMENT_COMPLETED: "✅",
            OrderStatus.PROCESSING: "🔄",
            OrderStatus.COMPLETED: "🎉",
            OrderStatus.FAILED: "❌",
            OrderStatus.REFUNDED: "💰",
            OrderStatus.CANCELLED: "🚫"
        }.get(order.status, "❓")
        
        text += (
            f"{status_emoji} <b>#{order.id}</b> | {order.uc_amount} UC\n"
            f"   👤 {order.user_id} | 🎮 {order.player_id}\n"
            f"   💰 {order.price:,} so'm | {order.created_at.strftime('%H:%M')}\n\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery):
    """Foydalanuvchilarni ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    from data.models import User
    from sqlalchemy import select, desc, func
    from data.database import db as database
    
    async with database.async_session() as session:
        # Jami foydalanuvchilar
        total_result = await session.execute(select(func.count(User.id)))
        total_users = total_result.scalar()
        
        # So'nggi foydalanuvchilar
        result = await session.execute(
            select(User).order_by(desc(User.created_at)).limit(10)
        )
        users = result.scalars().all()
    
    text = f"👥 <b>Foydalanuvchilar ({total_users} ta):</b>\n\n"
    for user in users:
        block_status = "🚫" if user.is_blocked else "✅"
        text += (
            f"{block_status} <b>{user.full_name}</b> (@{user.username or 'N/A'})\n"
            f"   ID: <code>{user.id}</code> | Buyurtmalar: {user.total_orders}\n"
            f"   Sarf: {user.total_spent:,.0f} so'm\n\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

@router.message(Command("block"))
async def cmd_block_user(message: Message):
    """Foydalanuvchini bloklash"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer(
                "❌ Format: /block <user_id> <sabab>\n"
                "Misol: /block 123456789 Spam"
            )
            return
        
        user_id = int(parts[1])
        reason = " ".join(parts[2:])
        
        await db.block_user(user_id, reason)
        
        await message.answer(
            f"🚫 Foydalanuvchi <code>{user_id}</code> bloklandi!\n"
            f"Sabab: {reason}",
            parse_mode="HTML"
        )
        
        # Foydalanuvchiga xabar
        try:
            await message.bot.send_message(
                user_id,
                f"❌ Sizning hisobingiz bloklandi!\nSabab: {reason}\n\n"
                f"Qo'llab-quvvatlash: @admin"
            )
        except:
            pass
            
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@router.message(Command("unblock"))
async def cmd_unblock_user(message: Message):
    """Blokdan chiqarish"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.split()[1])
        
        from data.database import db as database
        from data.models import User
        
        async with database.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.is_blocked = False
                user.block_reason = None
                await session.commit()
                
                await message.answer(f"✅ Foydalanuvchi <code>{user_id}</code> blokdan chiqarildi!", parse_mode="HTML")
                
                # Foydalanuvchiga xabar
                try:
                    await message.bot.send_message(user_id, "✅ Sizning hisobingiz blokdan chiqarildi!")
                except:
                    pass
            else:
                await message.answer("❌ Foydalanuvchi topilmadi!")
                
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot):
    """Barcha foydalanuvchilarga xabar yuborish"""
    if not is_admin(message.from_user.id):
        return
    
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❌ Xabar matnini kiriting!\nFormat: /broadcast <matn>")
        return
    
    await message.answer("⏳ Xabar yuborilmoqda...")
    
    from data.models import User
    from sqlalchemy import select
    from data.database import db as database
    
    async with database.async_session() as session:
        result = await session.execute(select(User.id))
        users = result.scalars().all()
    
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            await bot.send_message(user_id, f"📢 <b>Xabar:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit
        except:
            failed += 1
    
    await message.answer(
        f"✅ Yuborildi: {sent} ta\n"
        f"❌ Xatolik: {failed} ta"
    )

import asyncio