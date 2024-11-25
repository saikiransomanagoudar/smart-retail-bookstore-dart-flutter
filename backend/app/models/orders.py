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
        """Get 3 most recent orders for a specific user"""
        assert isinstance(user_id, str), f"user_id must be a string, got {type(user_id)}"
        db = SessionLocal()
        try:
            logging.info(f"Fetching orders for user_id: {user_id}")
            stmt = (
                select(
                    cls.order_id,
                    cls.purchase_date,
                    cls.expected_shipping_date
                )
                .where(cls.user_id == user_id)  # Ensure user_id is treated as a string
                .order_by(cls.purchase_date.desc())
                .limit(3)
            )
            logging.info(f"Generated SQL query: {stmt}")
            result = db.execute(stmt)
            orders = [
                {
                    "order_id": row["order_id"],
                    "purchase_date": row["purchase_date"].strftime("%Y-%m-%d %H:%M:%S"),
                    "expected_delivery": row["expected_shipping_date"].strftime("%Y-%m-%d"),
                }
                for row in result.mappings()
            ]
            logging.info(f"Orders fetched: {orders}")
            return orders
        except Exception as e:
            logging.error(f"Error fetching user orders: {str(e)}")
            return []
        finally:
            db.close()

    @classmethod
    def get_order_details(cls, order_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific order"""
        db = SessionLocal()
        try:
            # Query to get all items in the order
            stmt = (
                select(
                    cls.order_id,
                    cls.title,
                    cls.price,
                    cls.total_quantity,
                    cls.purchase_date,
                    cls.expected_shipping_date,
                    cls.street,
                    cls.city,
                    cls.state,
                    cls.zip_code,
                    cls.card_number,
                    cls.expiry_date
                )
                .where(cls.order_id == order_id)
            )

            logging.info(f"Generated SQL query: {stmt}")

            result = db.execute(stmt)
            rows = list(result.mappings())
            logging.info(f"Query returned {len(rows)} rows")
            if rows:
                logging.info(f"First row data: {dict(rows[0])}")

            items = []
            order_info = None
            total_amount = 0

            for row in rows:
                logging.info(f"Processing row: {dict(row)}")
                if not order_info:
                    order_info = {
                        "order_id": row['order_id'],
                        "purchase_date": row['purchase_date'].strftime("%Y-%m-%d %H:%M:%S"),
                        "expected_delivery": row['expected_shipping_date'].strftime("%Y-%m-%d"),
                        "shipping_address": {
                            "street": row['street'],
                            "city": row['city'],
                            "state": row['state'],
                            "zip_code": row['zip_code']
                        },
                        "payment_info": {
                            "card_number": row['card_number'],
                            "expiry_date": row['expiry_date']
                        }
                    }
                    logging.info(f"Created order_info: {order_info}")

                item_price = float(row['price'])
                item_quantity = int(row['total_quantity'])
                item = {
                    "title": row['title'],
                    "price": item_price,
                    "quantity": item_quantity,
                    "subtotal": item_price * item_quantity
                }
                items.append(item)
                total_amount += item_price * item_quantity
                logging.info(f"Added item: {item}")

            if order_info:
                order_info["items"] = items
                order_info["total_amount"] = total_amount
                logging.info(f"Final order details: {order_info}")
                return order_info

            logging.warning(f"No data found for order_id: {order_id}")
            return None

        except Exception as e:
            logging.error(f"Error fetching order details: {str(e)}")
            import traceback
            logging.error(f"Error traceback: {traceback.format_exc()}")
            return None
        finally:
            db.close()

    @classmethod
    def create_order(cls, cart_items: List[Dict[str, Any]], order_data: Dict[str, Any]) -> tuple[bool, str]:
        try:
            db = SessionLocal()
            # Generate a single order_id for all items in this order
            order_id = str(uuid.uuid4())
            purchase_time = datetime.utcnow()
            expected_delivery = purchase_time + timedelta(days=5)

            # Create an order item for each cart item with the same order_id
            for item in cart_items:
                new_order = cls(
                    order_id=order_id,  # Same order_id for all items in this order
                    user_id=order_data.get('user_id'),
                    title=item.get('title'),
                    price=float(item.get('Price', 0)),
                    total_quantity=int(item.get('quantity', 1)),
                    street=order_data.get('street'),
                    city=order_data.get('city'),
                    state=order_data.get('state'),
                    zip_code=order_data.get('zip_code'),
                    card_number=f"****{order_data.get('card_number')[-4:]}",
                    expiry_date=order_data.get('expiry_date'),
                    purchase_date=purchase_time,
                    expected_shipping_date=expected_delivery
                )
                db.add(new_order)

            db.commit()
            db.close()
            return True, order_id

        except Exception as e:
            logging.error(f"Error creating orders: {str(e)}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False, str(e)