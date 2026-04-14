"""
Admin Dashboard - Web interfeys (FastAPI)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
import uvicorn

from data.database import db
from data.models import Order, User, OrderStatus

app = FastAPI(title="PUBG UC Bot Admin Panel")
security = HTTPBasic()

class AdminDashboard:
    """Admin Dashboard"""
    
    def __init__(self):
        self.app = app
    
    async def verify_admin(self, credentials: HTTPBasicCredentials = Depends(security)):
        """Admin tekshiruvi"""
        # Bu yerda haqiqiy tekshirish bo'lishi kerak
        if credentials.username != "admin" or credentials.password != "password":
            raise HTTPException(status_code=401, detail="Noto'g'ri login")
        return credentials.username
    
    def setup_routes(self):
        """Routerlarni sozlash"""
        
        @app.get("/")
        async def dashboard():
            """Asosiy sahifa"""
            return {"message": "PUBG UC Bot Admin Panel", "status": "active"}
        
        @app.get("/stats")
        async def get_stats(username: str = Depends(self.verify_admin)):
            """Statistika"""
            today = datetime.utcnow().replace(hour=0, minute=0, second=0)
            
            async with db.async_session() as session:
                # Bugun
                today_orders = await session.execute(
                    select(func.count(Order.id), func.sum(Order.price))
                    .where(Order.created_at >= today)
                )
                orders_count, revenue = today_orders.one()
                
                # Status bo'yicha
                status_counts = await session.execute(
                    select(Order.status, func.count(Order.id))
                    .group_by(Order.status)
                )
                statuses = {str(s): c for s, c in status_counts.all()}
                
                return {
                    "today": {
                        "orders": orders_count or 0,
                        "revenue": revenue or 0
                    },
                    "statuses": statuses
                }
        
        @app.get("/orders")
        async def get_orders(
            limit: int = 50,
            offset: int = 0,
            username: str = Depends(self.verify_admin)
        ):
            """Buyurtmalar ro'yxati"""
            async with db.async_session() as session:
                result = await session.execute(
                    select(Order)
                    .order_by(desc(Order.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                orders = result.scalars().all()
                
                return [
                    {
                        "id": o.id,
                        "user_id": o.user_id,
                        "player_id": o.player_id,
                        "uc_amount": o.uc_amount,
                        "price": o.price,
                        "status": o.status.value,
                        "created_at": o.created_at.isoformat()
                    }
                    for o in orders
                ]
        
        @app.post("/orders/{order_id}/refund")
        async def refund_order(
            order_id: int,
            username: str = Depends(self.verify_admin)
        ):
            """Pul qaytarish"""
            async with db.async_session() as session:
                order = await session.get(Order, order_id)
                if not order:
                    raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
                
                order.status = OrderStatus.REFUNDED
                await session.commit()
                
                return {"success": True, "message": f"Order {order_id} refunded"}
        
        @app.get("/users")
        async def get_users(
            search: str = None,
            limit: int = 50,
            username: str = Depends(self.verify_admin)
        ):
            """Foydalanuvchilar"""
            async with db.async_session() as session:
                query = select(User).order_by(desc(User.created_at)).limit(limit)
                
                if search:
                    query = query.where(
                        (User.full_name.ilike(f"%{search}%")) |
                        (User.username.ilike(f"%{search}%"))
                    )
                
                result = await session.execute(query)
                users = result.scalars().all()
                
                return [
                    {
                        "id": u.id,
                        "username": u.username,
                        "full_name": u.full_name,
                        "is_blocked": u.is_blocked,
                        "total_orders": u.total_orders,
                        "total_spent": u.total_spent
                    }
                    for u in users
                ]

    def run(self, host="0.0.0.0", port=8000):
        """Ishga tushirish"""
        self.setup_routes()
        uvicorn.run(app, host=host, port=port)

# Global obyekt
dashboard = AdminDashboard()