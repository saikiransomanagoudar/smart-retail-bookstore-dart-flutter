# chatbot.py

import logging
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.chatbot_service import chatbot_service
from datetime import datetime, timedelta
from backend.app.models.orders import Order

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")
    metadata = data.get("metadata", {})
    
    try:
        response = await chatbot_service.chat({
            "message": user_input,
            "metadata": metadata
        })
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={
            "type": "error",
            "response": f"An error occurred: {str(e)}"
        }, status_code=500)

@router.post("/place-order")
async def place_order(request: Request):
    try:
        data = await request.json()
        logging.info(f"Received order data: {data}")  # Debug log
        
        if not isinstance(data, dict):
            return JSONResponse(
                content={"type": "error", "response": "Invalid request format"},
                status_code=400
            )

        # Extract the data from your actual frontend structure
        cart_items = []
        if "items" in data:
            cart_items = data["items"]
        elif "order_data" in data:
            cart_items = data["order_data"]

        user_details = data.get("user_details", {})

        # Debug logging
        logging.info(f"Parsed cart items: {cart_items}")
        logging.info(f"Parsed user details: {user_details}")

        if not cart_items:
            return JSONResponse(
                content={
                    "type": "error", 
                    "response": "Missing required data: No items found in order"
                },
                status_code=400
            )

        if not user_details:
            return JSONResponse(
                content={
                    "type": "error", 
                    "response": "Missing required data: No user details found"
                },
                status_code=400
            )

        # Create order in database
        success, order_id = Order.create_order(cart_items, user_details)
        
        if success:
            current_time = datetime.now()
            expected_delivery = (current_time + timedelta(days=3)).strftime("%Y-%m-%d")
            
            # Match your frontend's expected response format exactly
            return JSONResponse(content={
                "type": "order_confirmation",
                "response": {
                    "message": "Order placed successfully!",
                    "order_details": {
                        "order_id": order_id,
                        "total_cost": sum(float(item["price"]) * int(item.get("quantity", 1)) for item in cart_items),
                        "order_placed_on": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "expected_delivery": expected_delivery,
                        "status": "confirmed",
                        "items": cart_items
                    }
                }
            })
        else:
            return JSONResponse(
                content={
                    "type": "error",
                    "response": f"Failed to save order: {order_id}"
                },
                status_code=500
            )

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {str(e)}")
        return JSONResponse(
            content={
                "type": "error",
                "response": "Invalid JSON format"
            },
            status_code=400
        )
    except Exception as e:
        logging.error(f"Order placement error: {str(e)}")
        return JSONResponse(
            content={
                "type": "error",
                "response": f"An error occurred while placing the order: {str(e)}"
            },
            status_code=500
        )

@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})