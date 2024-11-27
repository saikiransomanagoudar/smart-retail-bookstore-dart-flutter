import traceback

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, select, and_
from backend.app.database.database import Base, SessionLocal
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
import uuid

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.user_id'))
    title = Column(String)
    price = Column(Float)
    total_quantity = Column(Integer, default=1)
    street = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    card_number = Column(String)
    expiry_date = Column(String)
    purchase_date = Column(DateTime)
    expected_shipping_date = Column(DateTime)

    @classmethod
    def get_user_orders(cls, user_id: str) -> List[Dict[str, Any]]:
        """Fetch the most recent orders for the specific user."""
        db = SessionLocal()
        try:
            # Fetch orders associated with the provided user_id
            stmt = (
                select(
                    cls.order_id,
                    cls.total_quantity,
                    cls.price,
                    cls.purchase_date,
                    cls.expected_shipping_date
                )
                .where(cls.user_id == user_id)  # Filter by user_id
                .order_by(cls.purchase_date.desc())
                .limit(5)  # Limit to the most recent 5 orders
            )
            result = db.execute(stmt)
            
            # Format the result as a list of dictionaries
            orders = [
                {
                    "order_id": row["order_id"],
                    "total_cost": row["price"] * row["total_quantity"],
                    "status": "Delivered" if datetime.now() > row["expected_shipping_date"] else "In Transit",
                    "items": [{"title": row["title"]}],  # Adjust if your schema allows multiple items
                    "expected_delivery": row["expected_shipping_date"].strftime("%Y-%m-%d"),
                }
                for row in result.mappings()
            ]
            return orders
        except Exception as e:
            logging.error(f"Error fetching user orders: {str(e)}")
            return []
        finally:
            db.close()

    @classmethod
    def get_user_orders(cls, user_id: str) -> List[Dict[str, Any]]:
        """Fetch the most recent orders for the specific user."""
        db = SessionLocal()
        try:
            # Fetch orders associated with the provided user_id
            stmt = (
                select(
                    cls.order_id,
                    cls.title,
                    cls.total_quantity,
                    cls.price,
                    cls.purchase_date,
                    cls.expected_shipping_date
                )
                .where(cls.user_id == user_id)  # Filter by user_id
                .order_by(cls.purchase_date.desc())
            )
            result = db.execute(stmt)
            
            # Format the result as a list of dictionaries
            orders = []
            for row in result.mappings():
                # Calculate total cost
                total_cost = float(row["price"]) * int(row["total_quantity"])
                
                orders.append({
                    "order_id": row["order_id"],
                    "title": row["title"],
                    "price": float(row["price"]),
                    "total_quantity": int(row["total_quantity"]),
                    "purchase_date": row["purchase_date"].strftime("%Y-%m-%d %H:%M:%S"),
                    "expected_delivery": row["expected_shipping_date"].strftime("%Y-%m-%d")
                })
            return orders
        except Exception as e:
            logging.error(f"Error fetching user orders: {str(e)}")
            return []
        finally:
            db.close()

    @classmethod
    def create_order(cls, cart_items: List[Dict[str, Any]], user_details: Dict[str, Any]) -> tuple[bool, str]:
        db = None
        try:
            db = SessionLocal()
            # Generate order ID in your desired format
            current_time = datetime.utcnow()
            order_id = f"ORD-{current_time.strftime('%Y%m%d%H%M%S')}"
            expected_delivery = current_time + timedelta(days=3)

            # Insert each cart item as part of the order
            for item in cart_items:
                new_order = cls(
                    order_id=order_id,
                    user_id=user_details.get('user_id'),
                    title=item.get('title'),
                    price=float(item.get('price', 0)),
                    total_quantity=int(item.get('quantity', 1)),
                    street=user_details.get('address', {}).get('street'),
                    city=user_details.get('address', {}).get('city'),
                    state=user_details.get('address', {}).get('state'),
                    zip_code=user_details.get('address', {}).get('zip_code'),
                    card_number=f"****{user_details.get('cardNumber', '')[-4:]}",
                    expiry_date=user_details.get('expiryDate'),
                    purchase_date=current_time,
                    expected_shipping_date=expected_delivery
                )
                db.add(new_order)

            # Commit transaction
            db.commit()
            return True, order_id

        except Exception as e:
            logging.error(f"Error creating orders: {str(e)}")
            if db:
                db.rollback()
            return False, str(e)

        finally:
            if db:
                db.close()
