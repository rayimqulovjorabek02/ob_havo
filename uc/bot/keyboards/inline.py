"""
Inline tugmalar
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import uc_prices

def get_main_menu() -> InlineKeyboardMarkup:
    """Asosiy menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 UC Sotib olish", callback_data="buy_uc")],
        [InlineKeyboardButton(text="💰 Narxlar", callback_data="prices")],
        [InlineKeyboardButton(text="📋 Buyurtmalarim", callback_data="my_orders")],
        [InlineKeyboardButton(text="❓ Yordam", callback_data="help")]
    ])

def get_uc_amounts() -> InlineKeyboardMarkup:
    """UC miqdorlari"""
    buttons = []
    for amount, data in uc_prices.PRICES.items():
        price = data["price"]
        bonus = data["bonus"]
        text = f"{amount} UC"
        if bonus > 0:
            text += f" +{bonus} 🎁"
        text += f" - {price:,} so'm"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"uc_{amount}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_methods(order_id: int) -> InlineKeyboardMarkup:
    """To'lov usullari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme", callback_data=f"pay_payme_{order_id}")],
        [InlineKeyboardButton(text="💳 Click", callback_data=f"pay_click_{order_id}")],
        [InlineKeyboardButton(text="💳 Uzcard/Humo", callback_data=f"pay_uzcard_{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_order_{order_id}")]
    ])

def get_check_payment(order_id: int) -> InlineKeyboardMarkup:
    """To'lovni tekshirish"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lov qildim", callback_data=f"check_payment_{order_id}")],
        [InlineKeyboardButton(text="🔄 To'lovga qaytish", callback_data=f"retry_payment_{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_order_{order_id}")]
    ])

def get_admin_menu() -> InlineKeyboardMarkup:
    """Admin menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📦 Buyurtmalar", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
        [InlineKeyboardButton(text="🔄 UC qayta yuborish", callback_data="admin_retry")]
    ])

def get_order_actions(order_id: int) -> InlineKeyboardMarkup:
    """Buyurtma boshqaruvi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{order_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{order_id}")],
        [InlineKeyboardButton(text="💰 Qaytarish", callback_data=f"refund_{order_id}")]
    ])