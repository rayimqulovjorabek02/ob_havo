"""
Validatsiya funksiyalari
"""

import re
from typing import Tuple, Optional

class Validator:
    """Barcha validatsiyalar"""
    
    @staticmethod
    def validate_player_id(player_id: str) -> Tuple[bool, Optional[str]]:
        """
        PUBG Player ID validatsiyasi
        
        Returns:
            (is_valid, error_message)
        """
        if not player_id:
            return False, "Player ID bo'sh bo'lishi mumkin emas"
        
        if not player_id.isdigit():
            return False, "Player ID faqat raqamlardan iborat bo'lishi kerak"
        
        if len(player_id) < 8 or len(player_id) > 12:
            return False, "Player ID 8-12 ta raqamdan iborat bo'lishi kerak"
        
        # PUBG ID diapazonlari
        pid = int(player_id)
        
        # Eski ID lar (2018-2020)
        is_old_range = 5000000000 <= pid <= 6999999999
        
        # Yangi ID lar (2020+)
        is_new_range = 100000000 <= pid <= 9999999999
        
        if not (is_old_range or is_new_range):
            return False, "Noto'g'ri Player ID diapazoni"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """Telefon raqam validatsiyasi (O'zbekiston)"""
        # +998 XX XXX XX XX formati
        pattern = r'^\+998\d{9}$'
        
        if not re.match(pattern, phone):
            return False, "Noto'g'ri format. To'g'ri format: +998901234567"
        
        return True, None
    
    @staticmethod
    def validate_amount(amount: str, min_val: int = 1000, max_val: int = 10000000) -> Tuple[bool, Optional[str]]:
        """Summa validatsiyasi"""
        try:
            value = int(amount.replace(" ", "").replace(",", ""))
            if value < min_val:
                return False, f"Minimal summa: {min_val:,} so'm"
            if value > max_val:
                return False, f"Maksimal summa: {max_val:,} so'm"
            return True, None
        except ValueError:
            return False, "Noto'g'ri summa formati"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Xavfsiz input tozalash"""
        # HTML taglarni olib tashlash
        text = re.sub(r'<[^>]+>', '', text)
        # Maxsus belgilarni olib tashlash
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
        return text.strip()

class InputSanitizer:
    """Input tozalash"""
    
    @staticmethod
    def clean_player_id(text: str) -> str:
        """Player ID tozalash"""
        # Faqat raqamlarni qoldirish
        return ''.join(filter(str.isdigit, text))
    
    @staticmethod
    def clean_phone(text: str) -> str:
        """Telefon raqam tozalash"""
        digits = ''.join(filter(str.isdigit, text))
        if digits.startswith('998'):
            digits = '+' + digits
        elif digits.startswith('9'):
            digits = '+998' + digits
        return digits
    
    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """Matnni qisqartirish"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text