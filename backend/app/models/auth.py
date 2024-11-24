# backend/app/models/auth.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database.database import Base
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# SQLAlchemy Model for database
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic Models for API
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse