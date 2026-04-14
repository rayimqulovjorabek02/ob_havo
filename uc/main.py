"""
PUBG UC Bot - Asosiy fayl
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from data.config import bot_config
from data.database import db
from bot.handlers import user, payment, admin

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")
    
    # Ma'lumotlar bazasini yaratish
    await db.create_tables()
    logger.info("Ma'lumotlar bazasi tayyor")
    
    # Adminlarga xabar
    for admin_id in bot_config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🚀 <b>Bot ishga tushdi!</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga xabar yuborish xatosi: {e}")

async def on_shutdown(bot: Bot):
    """Bot to'xtaganda"""
    logger.info("Bot to'xtatilmoqda...")
    
    # Adminlarga xabar
    for admin_id in bot_config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "⛔️ <b>Bot to'xtatildi!</b>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass

async def main():
    """Asosiy funksiya"""
    # Bot va Dispatcher
    bot = Bot(token=bot_config.TOKEN, parse_mode=ParseMode.HTML)
    
    # Storage (Redis yoki Memory)
    try:
        storage = RedisStorage.from_url("redis://localhost:6379/0")
    except:
        storage = MemoryStorage()
        logger.warning("Redis ishga tushmadi, MemoryStorage ishlatilmoqda")
    
    dp = Dispatcher(storage=storage)
    
    # Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(user.router)
    dp.include_router(payment.router)
    # dp.include_router(admin.router)  # Admin handlerlari
    
    # Startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Polling
    logger.info("Polling boshlandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi!")