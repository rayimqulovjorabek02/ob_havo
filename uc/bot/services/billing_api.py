"""
Payme va Click to'lov tizimlari integratsiyasi
"""

import aiohttp
import hashlib
import base64
from datetime import datetime
from typing import Dict, Optional
from data.config import payment_config
import logging

logger = logging.getLogger(__name__)

class PaymeAPI:
    """Payme API"""
    
    def __init__(self):
        self.merchant_id = payment_config.PAYME_MERCHANT_ID
        self.secret_key = payment_config.PAYME_SECRET_KEY
        self.test_mode = payment_config.PAYME_TEST_MODE
        self.base_url = "https://checkout.paycom.uz/api"
    
    def generate_payment_url(self, order_id: int, amount: float) -> str:
        """To'lov URL yaratish"""
        # amount so'mda, Payme tiyinda talab qiladi (1 so'm = 100 tiyin)
        amount_tiyin = int(amount * 100)
        
        params = {
            "merchant": self.merchant_id,
            "amount": amount_tiyin,
            "account[order_id]": order_id,
            "lang": "uz"
        }
        
        # URL yaratish
        import urllib.parse
        query = urllib.parse.urlencode(params)
        return f"https://checkout.paycom.uz/?{query}"
    
    def check_payment(self, payment_id: str) -> Dict:
        """To'lov holatini tekshirish (webhook orqali qilinadi)"""
        pass  # Webhook handler da amalga oshiriladi

class ClickAPI:
    """Click API"""
    
    def __init__(self):
        self.service_id = payment_config.CLICK_SERVICE_ID
        self.merchant_id = payment_config.CLICK_MERCHANT_ID
        self.secret_key = payment_config.CLICK_SECRET_KEY
        self.base_url = "https://api.click.uz/v2/merchant"
    
    def generate_payment_url(self, order_id: int, amount: float) -> str:
        """Click to'lov URL"""
        # Click API integratsiyasi
        return f"https://my.click.uz/services/pay?service_id={self.service_id}&merchant_id={self.merchant_id}&amount={amount}&transaction_param={order_id}"

class PaymentManager:
    """To'lov boshqaruvi"""
    
    def __init__(self):
        self.payme = PaymeAPI()
        self.click = ClickAPI()
    
    def get_payment_url(self, method: str, order_id: int, amount: float) -> str:
        """To'lov URL olish"""
        if method == "payme":
            return self.payme.generate_payment_url(order_id, amount)
        elif method == "click":
            return self.click.generate_payment_url(order_id, amount)
        else:
            return ""
    
    async def verify_payme_payment(self, data: dict) -> bool:
        """Payme to'lovini tekshirish"""
        # Payme webhook orqali kelgan ma'lumotni tekshirish
        # Bu qism server tomonida webhook handler da amalga oshiriladi
        pass

# Global obyekt
payment_manager = PaymentManager()