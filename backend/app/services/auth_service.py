from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.user import User
from ..core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def register_user(self, email: str, password: str):
        # Check if user exists
        existing_user = self.db.execute(
            "SELECT * FROM users WHERE email = :email",
            {"email": email}
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash the password
        hashed_password = self.get_password_hash(password)

        # Insert the new user into the database
        try:
            self.db.execute(
                "INSERT INTO users (email, password_hash) VALUES (:email, :password_hash)",
                {"email": email, "password_hash": hashed_password}
            )
            self.db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user: {str(e)}"
            )

        # Generate access token
        access_token = self.create_access_token({"sub": email})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": email}
        }

    async def login_user(self, email: str, password: str):
        # Retrieve the user from the database
        user = self.db.execute(
            "SELECT * FROM users WHERE email = :email",
            {"email": email}
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Verify the password
        if not self.verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Generate access token
        access_token = self.create_access_token({"sub": user["email"]})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": user["email"]}
        }
