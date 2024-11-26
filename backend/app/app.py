from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.app.api.recommendations import router as recommendations_router
# from backend.app.api.chatbot import router as chatbot_router
from backend.app.api.auth import router as auth_router
from backend.app.core.config import settings
from backend.app.database.database import create_tables

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["recommendations"])
# app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to the Book Recommendation System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)