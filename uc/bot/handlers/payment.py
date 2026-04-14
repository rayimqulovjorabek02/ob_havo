"""
To'lov va yetkazib berish handlerlari
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.services.seagm_api import seagm_api
from bot.keyboards.inline import get_main_menu
from data.database import db
from data.models import OrderStatus
from data.config import bot_config

import asyncio
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery, bot: Bot):
    """To'lov holatini tekshirish"""
    order_id = int(callback.data.split("_")[2])
    
    await callback.answer("⏳ To'lov tekshirilmoqda...")
    
    # Bu yerda to'lov tizimi API orqali tekshiriladi
    # Hozircha simulyatsiya qilamiz (haqiqiy loyihada webhook ishlatiladi)
    
    order = await db.get_order(order_id)
    if not order:
        await callback.message.edit_text("❌ Buyurtma topilmadi!")
        return
    
    # To'lov muvaffaqiyatli deb hisoblaymiz (test rejimi)
    # Haqiqiy loyihada: Payme/Click API orqali tekshirish
    payment_verified = True  # Test uchun
    
    if payment_verified:
        # To'lov qabul qilindi
        await db.update_order_status(
            order_id=order_id,
            status=OrderStatus.PAYMENT_COMPLETED,
            paid_at=datetime.utcnow()
        )
        
        await callback.message.edit_text(
            "✅ <b>To'lov qabul qilindi!</b>\n\n"
            "⏳ UC hisobingizga tushirilmoqda...\n"
            "Bu jarayon 5-15 daqiqa davom etadi.",
            parse_mode="HTML"
        )
        
        # UC yetkazib berish
        await process_uc_delivery(order_id, callback, bot)
    else:
        await callback.message.edit_text(
            "❌ <b>To'lov topilmadi!</b>\n\n"
            "Iltimos, to'lovni amalga oshiring va qayta urinib ko'ring.\n"
            "Yoki qo'llab-quvvatlash bilan bog'laning: /support",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

async def process_uc_delivery(order_id: int, callback: CallbackQuery, bot: Bot):
    """UC yetkazib berish"""
    order = await db.get_order(order_id)
    
    try:
        # SEAGM API orqali UC sotib olish
        result = await seagm_api.purchase_uc(
            player_id=order.player_id,
            uc_amount=order.uc_amount
        )
        
        if result["success"]:
            # Muvaffaqiyatli
            await db.update_order_status(
                order_id=order_id,
                status=OrderStatus.COMPLETED,
                seagm_order_id=result["order_id"],
                delivered_at=datetime.utcnow()
            )
            
            # Foydalanuvchi statistikasini yangilash
            await db.update_user_stats(order.user_id, order.price)
            
            # Muvaffaqiyat xabari
            await callback.message.edit_text(
                f"🎉 <b>Buyurtma bajarildi!</b>\n\n"
                f"✅ {order.uc_amount} UC hisobingizga tushirildi\n"
                f"🎮 Player ID: <code>{order.player_id}</code>\n"
                f"🔢 SEAGM Order: <code>{result['order_id']}</code>\n\n"
                f"📲 PUBG Mobile ni ochib, UC balansingizni tekshiring!\n\n"
                f"🙏 Xaridingiz uchun rahmat!",
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
            
            # Admin ga xabar
            await notify_admins(
                bot,
                f"✅ Yangi buyurtma bajarildi!\n\n"
                f"👤 User: {order.user_id}\n"
                f"🎮 Player ID: {order.player_id}\n"
                f"📦 {order.uc_amount} UC\n"
                f"💰 {order.price:,} so'm"
            )
            
        else:
            # Xatolik
            raise Exception(result.get("error", "Noma'lum xato"))
            
    except Exception as e:
        logger.error(f"UC yetkazib berish xatosi: {e}")
        
        await db.update_order_status(
            order_id=order_id,
            status=OrderStatus.FAILED,
            error_message=str(e),
            delivery_attempts=order.delivery_attempts + 1
        )
        
        await callback.message.edit_text(
            f"❌ <b>Yetkazib berishda xatolik!</b>\n\n"
            f"Xabar: {str(e)}\n\n"
            f"🔧 Texnik qo'llab-quvvatlash bilan bog'lanildi.\n"
            f"Tez orada muammo hal qilinadi.\n\n"
            f"Buyurtma ID: <code>#{order_id}</code>",
            parse_mode="HTML"
        )
        
        # Admin ga xabar
        await notify_admins(
            bot,
            f"🚨 <b>XATOLIK!</b>\n\n"
            f"Buyurtma: #{order_id}\n"
            f"Xato: {str(e)}\n\n"
            f"Tezroq tekshiring!"
        )

async def notify_admins(bot: Bot, message: str):
    """Adminlarga xabar yuborish"""
    for admin_id in bot_config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Admin ga xabar yuborish xatosi: {e}")

from datetime import datetime