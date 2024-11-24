# models/user.py
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from typing import List, Optional, Dict
from backend.app.database.database import Base


# Authentication User Model
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# User Preferences Model
class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(String, primary_key=True, index=True)
    favorite_books = Column(Text)
    favorite_authors = Column(Text)
    preferred_genres = Column(Text)
    themes_of_interest = Column(Text)
    reading_level = Column(String(50))


# Save user preferences
async def save_user_preferences(user_id: str, preferences: dict, db: Session):
    user_preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

    def list_to_string(lst: List[str]) -> str:
        return ', '.join(lst) if lst else ''

    if user_preferences:
        user_preferences.favorite_books = list_to_string(preferences["favorite_books"])
        user_preferences.favorite_authors = list_to_string(preferences["favorite_authors"])
        user_preferences.preferred_genres = list_to_string(preferences["preferred_genres"])
        user_preferences.themes_of_interest = list_to_string(preferences["themes_of_interest"])
        user_preferences.reading_level = preferences["reading_level"]
    else:
        new_preferences = UserPreferences(
            user_id=user_id,
            favorite_books=list_to_string(preferences["favorite_books"]),
            favorite_authors=list_to_string(preferences["favorite_authors"]),
            preferred_genres=list_to_string(preferences["preferred_genres"]),
            themes_of_interest=list_to_string(preferences["themes_of_interest"]),
            reading_level=preferences["reading_level"]
        )
        db.add(new_preferences)

    db.commit()


# Get user preferences
async def get_user_preferences(user_id: str, db: Session) -> Optional[Dict]:
    try:
        user_preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if user_preferences:
            def string_to_list(text: str) -> List[str]:
                return [x.strip() for x in text.split(',')] if text else []

            return {
                "user_id": user_preferences.user_id,
                "favorite_books": string_to_list(user_preferences.favorite_books),
                "favorite_authors": string_to_list(user_preferences.favorite_authors),
                "preferred_genres": string_to_list(user_preferences.preferred_genres),
                "themes_of_interest": string_to_list(user_preferences.themes_of_interest),
                "reading_level": user_preferences.reading_level
            }
        return None
    except Exception as e:
        print(f"Error retrieving user preferences: {str(e)}")
        return None


# Authentication Utility Functions
async def create_user(email: str, password_hash: str, db: Session) -> User:
    try:
        new_user = User(email=email, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None


async def get_user_by_email(email: str, db: Session) -> Optional[User]:
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        print(f"Error retrieving user by email: {str(e)}")
        return None
