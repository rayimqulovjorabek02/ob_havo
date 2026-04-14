"""
Konfiguratsiya fayli
Barcha maxfiy ma'lumotlar .env faylida saqlanadi
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    TOKEN: str = os.getenv("BOT_TOKEN")
    ADMIN_IDS: list = None
    
    def __post_init__(self):
        admin_ids = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_ids.split(",") if x.strip()]

@dataclass
class DatabaseConfig:
    HOST: str = os.getenv("DB_HOST", "localhost")
    PORT: int = int(os.getenv("DB_PORT", 5432))
    USER: str = os.getenv("DB_USER", "postgres")
    PASSWORD: str = os.getenv("DB_PASSWORD", "")
    NAME: str = os.getenv("DB_NAME", "pubg_uc_bot")
    
    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

@dataclass
class SEAGMConfig:
    """SEAGM API sozlamalari"""
    API_KEY: str = os.getenv("SEAGM_API_KEY")
    SECRET_KEY: str = os.getenv("SEAGM_SECRET_KEY")
    BASE_URL: str = "https://api.seagm.com/v2"
    TIMEOUT: int = 30

@dataclass
class PaymentConfig:
    """To'lov tizimlari sozlamalari"""
    # Payme
    PAYME_MERCHANT_ID: str = os.getenv("PAYME_MERCHANT_ID")
    PAYME_SECRET_KEY: str = os.getenv("PAYME_SECRET_KEY")
    PAYME_TEST_MODE: bool = os.getenv("PAYME_TEST_MODE", "False").lower() == "true"
    
    # Click
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID")
    CLICK_MERCHANT_ID: str = os.getenv("CLICK_MERCHANT_ID")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY")
    
    # Uzcard/Humo (Oson to'lov)
    OSOON_API_KEY: str = os.getenv("OSOON_API_KEY")

@dataclass
class UCPrices:
    """UC narxlari (so'm)"""
    PRICES = {
        60: {"price": 15000, "bonus": 0},
        325: {"price": 75000, "bonus": 0},
        660: {"price": 150000, "bonus": 0},
        1800: {"price": 380000, "bonus": 60},
        3850: {"price": 750000, "bonus": 150},
        8100: {"price": 1500000, "bonus": 400},
        16200: {"price": 2900000, "bonus": 900},
    }
    
    @classmethod
    def get_price(cls, amount: int) -> dict:
        return cls.PRICES.get(amount, {})

# Global konfiguratsiya obyektlari
bot_config = BotConfig()
db_config = DatabaseConfig()
seagm_config = SEAGMConfig()
payment_config = PaymentConfig()
uc_prices = UCPrices()