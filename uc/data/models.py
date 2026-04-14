"""
SQLAlchemy modellar
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, 
    DateTime, Boolean, ForeignKey, Enum, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class OrderStatus(enum.Enum):
    PENDING = "pending"           # Kutilmoqda
    PAYMENT_PENDING = "payment_pending"  # To'lov kutilmoqda
    PAYMENT_COMPLETED = "payment_completed"  # To'lov qilindi
    PROCESSING = "processing"     # UC yuborilmoqda
    COMPLETED = "completed"       # Bajarildi
    FAILED = "failed"             # Xatolik
    REFUNDED = "refunded"         # Pul qaytarildi
    CANCELLED = "cancelled"       # Bekor qilindi

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String(50), nullable=True)
    full_name = Column(String(100))
    phone = Column(String(20), nullable=True)
    language = Column(String(10), default="uz")
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Statistika
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    player_id = Column(String(20), nullable=False)  # PUBG Player ID
    uc_amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # So'mda
    bonus_uc = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # To'lov ma'lumotlari
    payment_method = Column(String(20), nullable=True)  # payme, click, uzcard
    payment_id = Column(String(100), nullable=True)    # To'lov tizimi ID
    paid_at = Column(DateTime, nullable=True)
    
    # UC yetkazib berish
    seagm_order_id = Column(String(100), nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    delivery_attempts = Column(Integer, default=0)
    
    # Xatolik va izohlar
    error_message = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    uc_amount = Column(Integer, nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(BigInteger, nullable=True)  # Admin ID

class AdminAction(Base):
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(50), nullable=False)  # block_user, refund, etc
    target_user_id = Column(BigInteger, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)