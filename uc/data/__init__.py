"""
Ma'lumotlar paketi
"""

from .database import db
from .config import (
    bot_config,
    db_config,
    seagm_config,
    payment_config,
    uc_prices
)

__all__ = [
    'db',
    'bot_config',
    'db_config',
    'seagm_config',
    'payment_config',
    'uc_prices'
]