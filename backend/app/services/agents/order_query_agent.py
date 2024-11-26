from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from datetime import datetime
import logging
import re
import json

from backend.app.models.orders import Order

class OrderQueryAgent:
    """Handles order status queries and tracking information"""
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.setup_prompts()
        self.user_id = None

    def setup_prompts(self):
        self.query_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an order query and tracking agent. Handle:
            1. Order status inquiries
            2. Order history requests
            3. Specific order detail requests
            4. Tracking information
            
            Provide clear, accurate information about orders and their current status."""),
            ("human", "{input}")
        ])

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process order query requests"""
        try:
            user_input = state.get("messages", [])[-1].content
            metadata = state.get("metadata", {})
            
            if isinstance(user_input, str):
                try:
                    user_input = json.loads(user_input)
                except:
                    pass  # Keep as string if not JSON

            user_id = metadata.get("user_id", "")
            if not user_id:
                return {
                    "type": "error",
                    "response": "User ID is required to query orders."
                }

            # Handle different types of queries
            if isinstance(user_input, dict) and user_input.get('metadata', {}).get('type') == 'order_details':
                return await self._handle_specific_order_query(user_input, user_id)
            elif isinstance(user_input, str):
                return await self._handle_text_query(user_input, user_id)
            else:
                return {
                    "type": "clarification",
                    "response": "Would you like to see your order history or check a specific order? Please provide more details."
                }

        except Exception as e:
            logging.error(f"Error processing order query: {str(e)}")
            return {
                "type": "error",
                "response": "An error occurred while processing your query. Please try again."
            }

    async def _handle_specific_order_query(self, user_input: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle queries for specific order details"""
        order_id = user_input['metadata'].get('order_id')
        if not order_id:
            return {
                "type": "error",
                "response": "Order ID is required for order details."
            }

        order_details = Order.get_order_details(order_id, user_id)
        if not order_details:
            return {
                "type": "error",
                "response": "Order not found or unauthorized access."
            }

        return {
            "type": "order_info",
            "response": self._format_order_details(order_details)
        }

    async def _handle_text_query(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Handle text-based order queries"""
        # Check for order ID in query
        if "order" in user_input.lower() and any(char.isdigit() for char in user_input):
            order_id = self._extract_order_id(user_input)
            if order_id:
                order_details = Order.get_order_details(order_id, user_id)
                if order_details:
                    return {
                        "type": "order_info",
                        "response": self._format_order_details(order_details)
                    }
                return {
                    "type": "error",
                    "response": "Order not found or unauthorized access."
                }

        # Check for order history request
        if any(keyword in user_input.lower() for keyword in ["orders", "history", "purchases"]):
            orders = Order.get_user_orders(user_id)
            if orders:
                return {
                    "type": "order_list",
                    "response": orders
                }
            return {
                "type": "error",
                "response": "No orders found."
            }

        return {
            "type": "clarification",
            "response": "Would you like to see your order history or check a specific order? Please provide more details."
        }

    def _extract_order_id(self, text: str) -> Optional[str]:
        """Extract order ID from text"""
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, text, re.IGNORECASE)
        return uuid_match.group(0) if uuid_match else None

    def _format_order_details(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """Format order details for response"""
        return {
            "order_id": order_details["order_id"],
            "total_cost": str(sum(item["subtotal"] for item in order_details["items"])),
            "order_placed_on": order_details["purchase_date"],
            "expected_delivery": order_details["expected_delivery"],
            "status": "Delivered" if datetime.now() > datetime.strptime(
                order_details["expected_delivery"], "%Y-%m-%d") else "In Transit",
            "message": "Order details retrieved successfully.",
            "shipping_address": order_details["shipping_address"],
            "items": order_details["items"]
        }