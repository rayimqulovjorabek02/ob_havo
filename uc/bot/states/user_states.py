"""
FSM (Finite State Machine) holatlari
"""

from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    """Foydalanuvchi holatlari"""
    MAIN_MENU = State()
    
    # UC sotib olish
    SELECTING_AMOUNT = State()
    ENTERING_PLAYER_ID = State()
    CONFIRMING_ORDER = State()
    
    # To'lov
    SELECTING_PAYMENT = State()
    WAITING_PAYMENT = State()
    
    # Qo'llab-quvvatlash
    WRITING_SUPPORT = State()

class AdminStates(StatesGroup):
    """Admin holatlari"""
    ADMIN_MENU = State()
    VIEWING_ORDERS = State()
    VIEWING_USERS = State()
    CHANGING_PRICE = State()
    SENDING_MESSAGE = State()