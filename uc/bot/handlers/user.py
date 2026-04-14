"""
Foydalanuvchi buyruqlari
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.inline import (
    get_main_menu, get_uc_amounts, get_payment_methods,
    get_check_payment
)
from bot.states.user_states import UserStates
from bot.services.security import security
from bot.services.billing_api import payment_manager
from data.database import db
from data.config import uc_prices, bot_config

import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start buyrug'i"""
    # Foydalanuvchini ro'yxatdan o'tkazish
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Bloklanganmi tekshirish
    if user.is_blocked:
        await message.answer(
            "❌ Sizning hisobingiz bloklangan.\n"
            f"Sabab: {user.block_reason}\n\n"
            "Qo'llab-quvvatlash: @admin"
        )
        return
    
    await state.set_state(UserStates.MAIN_MENU)
    
    await message.answer(
        f"👋 Salom, {message.from_user.full_name}!\n\n"
        "🎮 <b>PUBG Mobile UC</b> do'koniga xush kelibsiz!\n\n"
        "⚡️ Tezkor yetkazib berish\n"
        "🔒 100% xavfsizlik\n"
        "💳 Payme/Click/Uzcard orqali to'lov\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "buy_uc")
async def process_buy_uc(callback: CallbackQuery, state: FSMContext):
    """UC sotib olish bosqichi"""
    await state.set_state(UserStates.SELECTING_AMOUNT)
    
    await callback.message.edit_text(
        "🎮 <b>UC miqdorini tanlang:</b>\n\n"
        "💡 <i>Maslahat:</i> Ko'p miqdorda olsangiz, bonus UC olasiz!\n\n"
        "Quyidagi variantlardan birini tanlang:",
        reply_markup=get_uc_amounts(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("uc_"))
async def process_uc_selection(callback: CallbackQuery, state: FSMContext):
    """UC miqdori tanlandi"""
    uc_amount = int(callback.data.split("_")[1])
    price_data = uc_prices.get_price(uc_amount)
    
    if not price_data:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)
        return
    
    await state.update_data(
        uc_amount=uc_amount,
        price=price_data["price"],
        bonus=price_data["bonus"]
    )
    await state.set_state(UserStates.ENTERING_PLAYER_ID)
    
    bonus_text = f"\n🎁 Bonus: +{price_data['bonus']} UC" if price_data["bonus"] > 0 else ""
    
    await callback.message.edit_text(
        f"🛒 <b>Buyurtma:</b>\n"
        f"📦 UC miqdori: {uc_amount}{bonus_text}\n"
        f"💰 Narxi: {price_data['price']:,} so'm\n\n"
        f"✏️ Endi <b>PUBG Player ID</b> raqamingizni yuboring:\n\n"
        f"📝 <i>Player ID ni qayerdan olish:</i>\n"
        f"PUBG Mobile → Profil → Player ID (8-12 ta raqam)",
        parse_mode="HTML"
    )

@router.message(UserStates.ENTERING_PLAYER_ID)
async def process_player_id(message: Message, state: FSMContext):
    """Player ID qabul qilish"""
    player_id = message.text.strip()
    
    # Validatsiya
    if not player_id.isdigit() or len(player_id) < 8 or len(player_id) > 12:
        await message.answer(
            "❌ <b>Noto'g'ri Player ID!</b>\n\n"
            "Player ID faqat 8-12 ta raqamdan iborat bo'lishi kerak.\n"
            "Iltimos, qayta tekshiring va yuboring:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    uc_amount = data["uc_amount"]
    price = data["price"]
    bonus = data["bonus"]
    
    # Xavfsizlik tekshiruvi
    security_check = await security.check_user(
        user_id=message.from_user.id,
        player_id=player_id,
        uc_amount=uc_amount
    )
    
    if not security_check["allowed"]:
        await message.answer(
            "❌ <b>Buyurtma rad etildi!</b>\n\n"
            f"Sabab: {', '.join(security_check['warnings'])}\n\n"
            "Qo'llab-quvvatlash bilan bog'laning: /support",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    if security_check["action"] == "warn":
        # Ogohlantirish bilan davom etish
        await message.answer(
            f"⚠️ <b>Ogohlantirish:</b>\n"
            f"{', '.join(security_check['warnings'])}\n\n"
            f"Buyurtma davom ettirilsinmi?",
            reply_markup=get_confirmation_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Buyurtma yaratish
    order = await db.create_order(
        user_id=message.from_user.id,
        player_id=player_id,
        uc_amount=uc_amount,
        price=price,
        bonus_uc=bonus
    )
    
    await state.update_data(order_id=order.id)
    await state.set_state(UserStates.SELECTING_PAYMENT)
    
    bonus_text = f"\n🎁 Bonus UC: +{bonus}" if bonus > 0 else ""
    
    await message.answer(
        f"✅ <b>Buyurtma yaratildi!</b>\n\n"
        f"🆔 Buyurtma ID: <code>#{order.id}</code>\n"
        f"🎮 Player ID: <code>{player_id}</code>\n"
        f"📦 UC miqdori: {uc_amount}{bonus_text}\n"
        f"💰 To'lov summasi: {price:,} so'm\n\n"
        f"To'lov usulini tanlang:",
        reply_markup=get_payment_methods(order.id),
        parse_mode="HTML"
    )

def get_confirmation_keyboard():
    """Tasdiqlash tugmalari"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Davom etish", callback_data="confirm_proceed")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")]
    ])

@router.callback_query(F.data.startswith("pay_"))
async def process_payment_selection(callback: CallbackQuery, state: FSMContext):
    """To'lov usuli tanlandi"""
    parts = callback.data.split("_")
    method = parts[1]
    order_id = int(parts[2])
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi!", show_alert=True)
        return
    
    # To'lov URL yaratish
    payment_url = payment_manager.get_payment_url(
        method=method,
        order_id=order_id,
        amount=order.price
    )
    
    await db.update_order_status(
        order_id=order_id,
        status="payment_pending",
        payment_method=method
    )
    
    await state.set_state(UserStates.WAITING_PAYMENT)
    
    method_name = {
        "payme": "Payme",
        "click": "Click",
        "uzcard": "Uzcard/Humo"
    }.get(method, method)
    
    await callback.message.edit_text(
        f"💳 <b>{method_name} orqali to'lash</b>\n\n"
        f"Summasi: <b>{order.price:,} so'm</b>\n\n"
        f"👇 To'lov tugmasini bosing va to'lovni amalga oshiring:\n\n"
        f"⚠️ To'lov qilganingizdan so'ng 'To'lov qildim' tugmasini bosing!",
        reply_markup=get_check_payment(order_id),
        parse_mode="HTML"
    )
    
    # To'lov linkini alohida yuborish (URL tugma sifatida)
    await callback.message.answer(
        f"🔗 <a href='{payment_url}'>TO'LOVGA O'TISH</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.set_state(UserStates.MAIN_MENU)
    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery):
    """Narxlar ro'yxati"""
    text = "💰 <b>Joriy narxlar:</b>\n\n"
    for amount, data in uc_prices.PRICES.items():
        price = data["price"]
        bonus = data["bonus"]
        text += f"• {amount} UC"
        if bonus > 0:
            text += f" + <b>{bonus} 🎁</b>"
        text += f" — <code>{price:,}</code> so'm\n"
    
    text += "\n📉 <i>Narxlar o'zgarishi mumkin</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )