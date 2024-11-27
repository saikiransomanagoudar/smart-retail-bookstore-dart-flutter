from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging
from backend.app.models.orders import Order
import json
import re
from datetime import datetime

class OrderAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.state = "INIT"
        self.user_id = None
        self.setup_prompts()

    def setup_prompts(self):
        self.process_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an order processing, order status tracking agent for a bookstore. Help customers with:
            1. Guide customers through order placement:
            - Collect book selections
            - Ask for shipping information
            - Handle payment details
            2. Validate order information:
            - Ensure all required details are provided
            - Verify payment information format
            3. Provide clear order status updates:
            - Ask for the user's order ID to retrieve order details.
            4. Handle order history queries:
            - Provide a list of recent orders when no specific order ID is given.

            Respond in JSON format:
            {{
                "type": "order_response",
                "order_details": {{
                    "order_id": "<order_id>",
                    "total_cost": <total_cost>,
                    "status": "<status>",
                    "items": [...],
                    "expected_delivery": "<expected_delivery>"
                }},
                "message": "<response_message>"
            }}"""),
            ("human", "{input}")
        ])

    async def process_query(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user queries about orders"""
        try:
            # If asking about orders/history
            if any(keyword in user_input.lower() for keyword in ["orders", "history", "purchases"]):
                # Actually call the Order model to get real orders
                orders = Order.get_user_orders(user_id)
                if orders:
                    # Use the actual orders from database
                    return {
                        "type": "order_response",
                        "response": {
                            "message": "Here are your recent orders:",
                            "order_details": orders
                        }
                    }
                return {
                    "type": "error",
                    "response": "No orders found."
                }

            # If asking about specific order
            if "order" in user_input.lower() and any(char.isdigit() for char in user_input):
                order_id = self.extract_order_id(user_input)
                if order_id:
                    # Actually call the Order model to get specific order
                    order_details = Order.get_order_details(order_id, user_id)
                    if order_details:
                        return {
                            "type": "order_info",
                            "response": order_details
                        }
                    return {
                        "type": "error",
                        "response": "Order not found or unauthorized access."
                    }

            # For general order-related queries, use LLM
            return {
                "type": "clarification",
                "response": "Would you like to see your order history or check a specific order? Please provide more details."
            }

        except Exception as e:
            logging.error(f"Error processing order query: {str(e)}")
            return {
                "type": "error",
                "response": "An error occurred while retrieving your order information."
            }

    def extract_order_id(self, text: str) -> str:
        """Extract order ID from user input"""
        import re
        # Look for UUID pattern
        uuid_pattern = r'user_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, text, re.IGNORECASE)
        if uuid_match:
            return uuid_match.group(0)
        return None
    
    async def process_query(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user queries about orders"""
        try:
            # If asking about orders/history
            if any(keyword in user_input.lower() for keyword in ["orders", "history", "purchases"]):
                # Actually call the Order model to get real orders
                orders = Order.get_user_orders(user_id)
                if orders:
                    # Use the actual orders from database
                    return {
                        "type": "order_response",
                        "response": {
                            "message": "Here are your recent orders:",
                            "order_details": orders
                        }
                    }
                return {
                    "type": "error",
                    "response": "No orders found."
                }

            # If asking about specific order
            if "order" in user_input.lower() and any(char.isdigit() for char in user_input):
                order_id = self.extract_order_id(user_input)
                if order_id:
                    # Actually call the Order model to get specific order
                    order_details = Order.get_order_details(order_id, user_id)
                    if order_details:
                        return {
                            "type": "order_info",
                            "response": order_details
                        }
                    return {
                        "type": "error",
                        "response": "Order not found or unauthorized access."
                    }

            # For general order-related queries, use LLM
            return {
                "type": "clarification",
                "response": "Would you like to see your order history or check a specific order? Please provide more details."
            }

        except Exception as e:
            logging.error(f"Error processing order query: {str(e)}")
            return {
                "type": "error",
                "response": "An error occurred while retrieving your order information."
            }
        
    def _validate_order_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data before processing"""
        try:
            order_data = data.get("order_data", [])
            user_details = data.get("user_details", {})

            # Validate cart items
            if not order_data:
                return {
                    "is_valid": False,
                    "error": "Cart is empty"
                }

            for item in order_data:
                missing_keys = [key for key in ['title', 'price', 'quantity'] if key not in item]
                if missing_keys:
                    return {
                        "is_valid": False,
                        "error": f"Invalid cart item format. Missing keys: {', '.join(missing_keys)} in item: {item}"
                    }

            # Validate user details
            required_fields = {
                'user_id': 'User ID',
                'address': 'Address',
                'cardNumber': 'Card number',
                'expiryDate': 'Card expiry date',
                'cvv': 'CVV'
            }

            missing_fields = [field_name for field, field_name in required_fields.items() 
                            if field not in user_details]
            
            if missing_fields:
                return {
                    "is_valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }

            # Validate address
            address = user_details.get('address', {})
            required_address_fields = {
                'street': 'Street address',
                'city': 'City',
                'state': 'State',
                'zip_code': 'ZIP code'
            }

            missing_address_fields = [field_name for field, field_name in required_address_fields.items() 
                                    if field not in address]
            
            if missing_address_fields:
                return {
                    "is_valid": False,
                    "error": f"Missing address fields: {', '.join(missing_address_fields)}"
                }

            # Validate payment information
            card_number = user_details.get('cardNumber', '')
            expiry_date = user_details.get('expiryDate', '')
            cvv = user_details.get('cvv', '')

            if not card_number.isdigit() or len(card_number) != 16:
                return {
                    "is_valid": False,
                    "error": "Invalid card number. Must be 16 digits."
                }

            if not re.match(r'^\d{2}/\d{2}$', expiry_date):
                return {
                    "is_valid": False,
                    "error": "Invalid expiry date. Must be in MM/YY format."
                }

            if not cvv.isdigit() or len(cvv) != 3:
                return {
                    "is_valid": False,
                    "error": "Invalid CVV. Must be 3 digits."
                }

            return {
                "is_valid": True,
                "error": None
            }

        except Exception as e:
            logging.error(f"Error validating order data: {str(e)}")
            return {
                "is_valid": False,
                "error": "Error validating order data"
            }

    async def _format_order_confirmation(self, order_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format order confirmation response"""
        try:
            return {
                "type": "order_confirmation",
                "response": {
                    "order_id": order_response.get("order_id"),
                    "total_cost": order_response.get("total_cost"),
                    "order_placed_on": order_response.get("order_placed_on"),
                    "expected_delivery": order_response.get("expected_delivery"),
                    "message": "Thank you for your order! Here are your order details:"
                }
            }
        except Exception as e:
            logging.error(f"Error formatting order confirmation: {str(e)}")
            return {
                "type": "error",
                "response": "Error formatting order confirmation"
            }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-related requests"""
        try:
            messages = state.get("messages", [])
            last_message = messages[-1].content if messages else ""
            
            # Try to parse as JSON for order placement
            try:
                if isinstance(last_message, str) and (last_message.startswith('{') or isinstance(last_message, dict)):
                    data = last_message if isinstance(last_message, dict) else json.loads(last_message)
                    if "order_data" in data and "user_details" in data:
                        validation_result = self._validate_order_data(data)
                        if validation_result['is_valid']:
                            return {
                                "type": "order_processing",
                                "response": {
                                    "data": data,
                                    "message": "Order data validated successfully. Would you like to proceed with placing the order?"
                                }
                            }
                        else:
                            return {
                                "type": "error",
                                "response": f"Order validation failed: {validation_result['error']}"
                            }
            except json.JSONDecodeError:
                pass

            # Handle regular text messages
            if isinstance(last_message, str):
                if "place order" in last_message.lower() or "buy" in last_message.lower():
                    return {
                        "type": "order",
                        "response": "I'll help you place your order. Please provide the following details:\n"
                                  "1. Shipping address\n"
                                  "2. Payment information\n\n"
                                  "You can also add items to your cart and I'll guide you through the process."
                    }

            # Use LLM for general order-related queries
            chain = self.process_prompt | self.llm
            response = await chain.ainvoke({"input": last_message})
            
            return {
                "type": "order",
                "response": response.content
            }

        except Exception as e:
            logging.error(f"Error in order processing: {str(e)}")
            return {
                "type": "error",
                "response": "I encountered an error processing your request. Please try again."
            }