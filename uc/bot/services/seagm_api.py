"""
SEAGM API integratsiyasi - Xavfsiz va ishonchli
"""

import aiohttp
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional
from data.config import seagm_config
import logging

logger = logging.getLogger(__name__)

class SEAGMAPI:
    """SEAGM API bilan ishlash"""
    
    def __init__(self):
        self.api_key = seagm_config.API_KEY
        self.secret_key = seagm_config.SECRET_KEY
        self.base_url = seagm_config.BASE_URL
        self.timeout = seagm_config.TIMEOUT
    
    def _generate_signature(self, params: dict) -> str:
        """API so'rov imzosini yaratish"""
        # SEAGM talab qiladigan imzo formati
        sorted_params = sorted(params.items())
        sign_string = f"{self.api_key}{json.dumps(dict(sorted_params))}{self.secret_key}"
        return hashlib.md5(sign_string.encode()).hexdigest()
    
    async def _make_request(self, endpoint: str, data: dict = None, method: str = "POST") -> dict:
        """API so'rov yuborish"""
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key
        }
        
        if data:
            data["timestamp"] = int(datetime.now().timestamp())
            data["signature"] = self._generate_signature(data)
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(
                        url, 
                        json=data, 
                        headers=headers, 
                        timeout=self.timeout
                    ) as response:
                        result = await response.json()
                        logger.info(f"SEAGM API response: {result}")
                        return result
                else:
                    async with session.get(
                        url, 
                        params=data, 
                        headers=headers, 
                        timeout=self.timeout
                    ) as response:
                        result = await response.json()
                        return result
                        
        except asyncio.TimeoutError:
            logger.error("SEAGM API timeout")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"SEAGM API error: {e}")
            return {"success": False, "error": str(e)}
    
    async def purchase_uc(
        self, 
        player_id: str, 
        uc_amount: int,
        server: str = "PUBG_MOBILE_GLOBAL"
    ) -> Dict:
        """
        UC sotib olish va yetkazib berish
        
        Args:
            player_id: PUBG Player ID
            uc_amount: UC miqdori (60, 325, 660, 1800, 3850, 8100, 16200)
            server: Server kodi (PUBG_MOBILE_GLOBAL, PUBG_MOBILE_TR, etc)
        
        Returns:
            dict: Buyurtma natijasi
        """
        endpoint = "order/create"
        
        payload = {
            "game": "PUBG_MOBILE",
            "server": server,
            "product": f"UC_{uc_amount}",
            "player_id": player_id,
            "quantity": 1,
            "validate_player": True  # Player ID tekshiruvi
        }
        
        result = await self._make_request(endpoint, payload)
        
        if result.get("code") == 200:
            return {
                "success": True,
                "order_id": result["data"]["order_id"],
                "status": result["data"]["status"],
                "message": "Buyurtma muvaffaqiyatli yaratildi"
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Noma'lum xato"),
                "code": result.get("code")
            }
    
    async def check_order_status(self, seagm_order_id: str) -> Dict:
        """Buyurtma holatini tekshirish"""
        endpoint = "order/status"
        
        payload = {
            "order_id": seagm_order_id
        }
        
        result = await self._make_request(endpoint, payload, method="GET")
        
        if result.get("code") == 200:
            return {
                "success": True,
                "status": result["data"]["status"],  # pending, processing, completed, failed
                "details": result["data"]
            }
        else:
            return {
                "success": False,
                "error": result.get("message")
            }
    
    async def validate_player_id(self, player_id: str, server: str = "PUBG_MOBILE_GLOBAL") -> bool:
        """Player ID mavjudligini tekshirish"""
        # Bu funksiya SEAGM API da mavjud bo'lmasa, 
        # buyurtma yaratishdan oldin tekshirish uchun ishlatiladi
        test_result = await self.purchase_uc(
            player_id=player_id,
            uc_amount=60,  # Minimal miqdor
            server=server
        )
        
        # Agar player ID noto'g'ri bo'lsa, xato qaytaradi
        if "invalid player" in test_result.get("error", "").lower():
            return False
        return True

# Global API obyekti
seagm_api = SEAGMAPI()