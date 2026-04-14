"""
Xavfsizlik tekshiruvlari va anti-fraud
"""

from datetime import datetime, timedelta
from typing import Dict, List
from data.database import db
import logging

logger = logging.getLogger(__name__)

class SecurityChecker:
    """Xavfsizlik tekshiruvlari"""
    
    def __init__(self):
        self.suspicious_patterns = {
            "rapid_orders": 5,      # 1 soat ichida 5+ buyurtma
            "multiple_players": 3,   # 1 soat ichida 3+ turli player ID
            "large_amounts": 3,      # Bir kunda 3+ katta buyurtma (>1000 UC)
        }
    
    async def check_user(self, user_id: int, player_id: str, uc_amount: int) -> Dict:
        """
        Foydalanuvchini to'liq tekshirish
        
        Returns:
            dict: {
                "allowed": bool,
                "risk_level": str (low, medium, high),
                "warnings": list,
                "action": str (allow, warn, block)
            }
        """
        warnings = []
        risk_score = 0
        
        # 1. Bloklangan foydalanuvchi tekshiruvi
        user = await db.get_user(user_id)
        if user and user.is_blocked:
            return {
                "allowed": False,
                "risk_level": "high",
                "warnings": ["Foydalanuvchi bloklangan"],
                "action": "block"
            }
        
        # 2. So'nggi buyurtmalarni tekshirish
        from data.models import Order
        from sqlalchemy import select, func
        from data.database import db as database
        
        async with database.async_session() as session:
            # So'nggi 1 soatdagi buyurtmalar
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_orders_result = await session.execute(
                select(Order).where(
                    Order.user_id == user_id,
                    Order.created_at >= one_hour_ago
                )
            )
            recent_orders = recent_orders_result.scalars().all()
            
            # Tez-tez buyurtma tekshiruvi
            if len(recent_orders) >= self.suspicious_patterns["rapid_orders"]:
                warnings.append(f"1 soat ichida {len(recent_orders)} ta buyurtma")
                risk_score += 2
            
            # Turli Player ID tekshiruvi
            unique_players = len(set(o.player_id for o in recent_orders))
            if unique_players >= self.suspicious_patterns["multiple_players"]:
                warnings.append(f"1 soat ichida {unique_players} ta turli Player ID")
                risk_score += 3
            
            # Katta miqdor tekshiruvi
            today = datetime.utcnow().replace(hour=0, minute=0, second=0)
            today_orders_result = await session.execute(
                select(func.sum(Order.uc_amount)).where(
                    Order.user_id == user_id,
                    Order.created_at >= today
                )
            )
            today_total = today_orders_result.scalar() or 0
            
            if today_total + uc_amount > 5000:  # Kuniga 5000 UC dan ko'p
                warnings.append(f"Katta miqdor: bugun {today_total + uc_amount} UC")
                risk_score += 2
        
        # 3. Player ID validatsiyasi
        if not self._validate_player_id_format(player_id):
            warnings.append("Noto'g'ri Player ID formati")
            risk_score += 1
        
        # 4. Vaqt mintaqasi tekshiruvi (ixtiyoriy)
        # Agar foydalanuvchi g'alati vaqtda faol bo'lsa
        hour = datetime.utcnow().hour
        if hour < 5 or hour > 23:  # Tungi vaqt
            warnings.append("G'alati vaqt faolligi")
            risk_score += 1
        
        # Xulosa
        if risk_score >= 5:
            return {
                "allowed": False,
                "risk_level": "high",
                "warnings": warnings,
                "action": "block"
            }
        elif risk_score >= 2:
            return {
                "allowed": True,
                "risk_level": "medium",
                "warnings": warnings,
                "action": "warn"
            }
        else:
            return {
                "allowed": True,
                "risk_level": "low",
                "warnings": [],
                "action": "allow"
            }
    
    def _validate_player_id_format(self, player_id: str) -> bool:
        """Player ID formatini tekshirish"""
        if not player_id.isdigit():
            return False
        
        if len(player_id) < 8 or len(player_id) > 12:
            return False
        
        # PUBG ID diapazonlari
        pid = int(player_id)
        # Eski ID lar
        if 5000000000 <= pid <= 6999999999:
            return True
        # Yangi ID lar
        if 100000000 <= pid <= 9999999999:
            return True
        
        return False
    
    async def log_suspicious_activity(self, user_id: int, activity: str, details: str):
        """Shubhali faollikni qayd etish"""
        logger.warning(f"Shubhali faollik: User {user_id}, {activity}, {details}")
        # Bu yerda admin ga xabar yuborish yoki bazaga yozish mumkin

# Global obyekt
security = SecurityChecker()