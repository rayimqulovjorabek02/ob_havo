"""
Yordamchi funksiyalar
"""

import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional

class Helpers:
    """Yordamchi funksiyalar"""
    
    @staticmethod
    def generate_order_id() -> str:
        """Tasodifiy buyurtma ID yaratish"""
        # Format: UC-XXXXXX (6 ta raqam)
        numbers = ''.join(random.choices(string.digits, k=6))
        return f"UC{numbers}"
    
    @staticmethod
    def generate_payment_id() -> str:
        """To'lov ID yaratish"""
        timestamp = int(datetime.now().timestamp())
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PAY-{timestamp}-{random_part}"
    
    @staticmethod
    def format_price(price: float) -> str:
        """Narxni formatlash"""
        return f"{price:,.0f}".replace(",", " ")
    
    @staticmethod
    def format_date(date: datetime) -> str:
        """Sana formatlash"""
        return date.strftime("%d.%m.%Y %H:%M")
    
    @staticmethod
    def time_ago(date: datetime) -> str:
        """Vaqt farqini human-readable formatda"""
        now = datetime.utcnow()
        diff = now - date
        
        if diff < timedelta(minutes=1):
            return "Hozirgina"
        elif diff < timedelta(hours=1):
            return f"{int(diff.seconds / 60)} daqiqa oldin"
        elif diff < timedelta(days=1):
            return f"{int(diff.seconds / 3600)} soat oldin"
        else:
            return f"{diff.days} kun oldin"
    
    @staticmethod
    def calculate_bonus(uc_amount: int) -> int:
        """Bonus UC hisoblash"""
        # Bonus foizi: 5-10%
        if uc_amount >= 8100:
            return int(uc_amount * 0.10)
        elif uc_amount >= 3850:
            return int(uc_amount * 0.08)
        elif uc_amount >= 1800:
            return int(uc_amount * 0.05)
        return 0
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Maxfiy ma'lumotlarni hashlash"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

class Logger:
    """Log yordamchisi"""
    
    @staticmethod
    def log_order_created(user_id: int, order_id: int, amount: int):
        """Buyurtma yaratildi logi"""
        print(f"[{datetime.now()}] 🛒 Order created: User={user_id}, Order={order_id}, Amount={amount} UC")
    
    @staticmethod
    def log_payment_received(order_id: int, method: str, amount: float):
        """To'lov qabul qilindi logi"""
        print(f"[{datetime.now()}] 💰 Payment received: Order={order_id}, Method={method}, Amount={amount}")
    
    @staticmethod
    def log_uc_delivered(order_id: int, player_id: str, amount: int):
        """UC yetkazildi logi"""
        print(f"[{datetime.now()}] ✅ UC delivered: Order={order_id}, Player={player_id}, Amount={amount}")
    
    @staticmethod
    def log_error(context: str, error: str):
        """Xatolik logi"""
        print(f"[{datetime.now()}] ❌ ERROR in {context}: {error}")

class RateLimiter:
    """So'rovlar cheklash"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, user_id: int, max_requests: int = 5, window_seconds: int = 60) -> bool:
        """Foydalanuvchi so'rovini tekshirish"""
        now = datetime.utcnow()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Eski so'rovlarni tozalash
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).seconds < window_seconds
        ]
        
        if len(self.requests[user_id]) >= max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining_time(self, user_id: int, window_seconds: int = 60) -> int:
        """Qolgan vaqtni hisoblash"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest_request = min(self.requests[user_id])
        elapsed = (datetime.utcnow() - oldest_request).seconds
        return max(0, window_seconds - elapsed)

# Global obyektlar
helpers = Helpers()
logger = Logger()
rate_limiter = RateLimiter()