from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.chatbot_service import chatbot_service

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")

    try:
        response = await chatbot_service.chat(user_input)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={
            "type": "error",
            "response": f"An error occurred: {str(e)}"
        }, status_code=500)

@router.post("/place-order")
async def place_order(request: Request):
    data = await request.json()
    order_data = data.get("order_data")
    user_details = data.get("user_details")

    if not order_data or not user_details:
        return JSONResponse(content={
            "type": "error",
            "response": "Invalid input format. Please provide both cart (`order_data`) and user details (`user_details`)."
        }, status_code=400)

    try:
        combined_data = {
            "order_data": order_data,
            "user_details": user_details
        }
        response = await chatbot_service.place_order(combined_data)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={
            "type": "error",
            "response": f"An error occurred while placing the order: {str(e)}"
        }, status_code=500)

@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})