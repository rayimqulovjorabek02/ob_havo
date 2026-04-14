"""
Asinxron ma'lumotlar bazasi boshqaruvi
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from data.models import Base
from data.config import db_config

class Database:
    def __init__(self):
        self.engine = create_async_engine(
            db_config.URL,
            echo=False,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Jadvallarni yaratish"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self):
        """Sessiya generatori"""
        async with self.async_session() as session:
            yield session
    
    # User metodlari
    async def get_or_create_user(self, user_id: int, username: str, full_name: str):
        from data.models import User
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    full_name=full_name
                )
                session.add(user)
                await session.commit()
            return user
    
    async def get_user(self, user_id: int):
        from data.models import User
        async with self.async_session() as session:
            return await session.get(User, user_id)
    
    async def block_user(self, user_id: int, reason: str):
        from data.models import User
        async with self.async_session() as session:
            user = await session.get(User, user_id)
            if user:
                user.is_blocked = True
                user.block_reason = reason
                await session.commit()
    
    # Order metodlari
    async def create_order(self, user_id: int, player_id: str, uc_amount: int, price: float, bonus_uc: int = 0):
        from data.models import Order, OrderStatus
        async with self.async_session() as session:
            order = Order(
                user_id=user_id,
                player_id=player_id,
                uc_amount=uc_amount,
                price=price,
                bonus_uc=bonus_uc,
                status=OrderStatus.PENDING
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order
    
    async def get_order(self, order_id: int):
        from data.models import Order
        async with self.async_session() as session:
            return await session.get(Order, order_id)
    
    async def update_order_status(self, order_id: int, status, **kwargs):
        from data.models import Order
        async with self.async_session() as session:
            order = await session.get(Order, order_id)
            if order:
                order.status = status
                for key, value in kwargs.items():
                    setattr(order, key, value)
                await session.commit()
            return order
    
    async def get_pending_orders(self):
        from data.models import Order, OrderStatus
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(Order).where(Order.status == OrderStatus.PAYMENT_COMPLETED)
            )
            return result.scalars().all()
    
    # Statistika
    async def get_stats(self, period: str = "today"):
        from data.models import Order, User, OrderStatus
        from sqlalchemy import func, select
        from datetime import datetime, timedelta
        
        async with self.async_session() as session:
            if period == "today":
                start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif period == "month":
                start_date = datetime.utcnow() - timedelta(days=30)
            else:
                start_date = datetime(2000, 1, 1)
            
            # Buyurtmalar statistikasi
            orders_result = await session.execute(
                select(
                    func.count(Order.id).label("total"),
                    func.sum(Order.price).label("revenue")
                ).where(Order.created_at >= start_date)
            )
            orders_stats = orders_result.one()
            
            # Foydalanuvchilar soni
            users_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= start_date)
            )
            new_users = users_result.scalar()
            
            # Status bo'yicha
            pending_result = await session.execute(
                select(func.count(Order.id)).where(
                    Order.status == OrderStatus.PENDING
                )
            )
            pending = pending_result.scalar()
            
            return {
                "total_orders": orders_stats.total or 0,
                "total_revenue": orders_stats.revenue or 0,
                "new_users": new_users,
                "pending_orders": pending
            }

# Global database obyekti
db = Database()