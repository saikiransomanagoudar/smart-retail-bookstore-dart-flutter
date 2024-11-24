# recommendations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.database.database import get_db
from backend.app.services.recommendation_service import get_recommendations
from backend.app.services.recommendation_service import get_trending_books as get_trending_books_service
from backend.app.models.user import save_user_preferences, get_user_preferences

router = APIRouter()

class UserPreferencesInput(BaseModel):
    user_id: str
    favorite_books: List[str]
    favorite_authors: List[str]
    preferred_genres: List[str]
    themes_of_interest: List[str]
    reading_level: str

    class Config:
        from_attributes = True

class BookRecommendation(BaseModel):
    id: int
    title: str
    release_year: Optional[int] = None
    release_date: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    pages: Optional[int] = None
    genres: Optional[List[str]] = None
    price: float

@router.post("/initial-recommendations")
async def initial_recommendations(request: dict, db: Session = Depends(get_db)):
    try:
        user_id = request.get("userId")
        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")

        recommendations = await get_recommendations(user_id, db)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-books", response_model=List[BookRecommendation])
async def get_trending_book():
    try:
        trending_books = await get_trending_books_service()
        return trending_books
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching trending books")

@router.post("/preferences")
async def save_preferences(preferences: UserPreferencesInput, db: Session = Depends(get_db)):
    try:
        await save_user_preferences(preferences.user_id, preferences.model_dump(), db)
        return {"message": "Preferences saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_id}")
async def get_user_preferences_endpoint(user_id: str, db: Session = Depends(get_db)):
    try:
        preferences = await get_user_preferences(user_id, db)
        if preferences:
            return preferences
        else:
            raise HTTPException(status_code=404, detail="User preferences not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching user preferences")