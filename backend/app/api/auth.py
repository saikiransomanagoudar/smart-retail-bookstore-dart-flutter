import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from ..database.database import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"

# Define Pydantic models for request bodies
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.execute(
        "SELECT * FROM users WHERE email = :email", {"email": request.email}
    ).fetchone()

    if existing_user:
        return {
            "success": False,
            "message": "User already registered"
        }

    # Hash the password
    hashed_password = pwd_context.hash(request.password)

    # Insert the user into the database
    try:
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)",
            {"email": request.email, "password_hash": hashed_password},
        )
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {str(e)}"
        )

    return {
        "success": True,
        "message": "User created successfully"
    }

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Retrieve the user
    result = db.execute(
        "SELECT * FROM users WHERE email = :email", {"email": request.email}
    ).fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify the password
    if not pwd_context.verify(request.password, result["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Generate a JWT token
    token = jwt.encode({"sub": result["email"]}, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer"
    }
