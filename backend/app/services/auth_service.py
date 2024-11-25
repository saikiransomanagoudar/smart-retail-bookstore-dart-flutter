from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
import uuid
from ..database.database import get_db
from ..models.user import User
from ..core.config import settings
from fastapi.responses import JSONResponse

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
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.email == email).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Generate custom user ID
            custom_user_id = f"user_{uuid.uuid4()}"

            # Create new user
            new_user = User(
                user_id=custom_user_id,
                email=email,
                password_hash=self.get_password_hash(password)
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            # Generate access token
            access_token = self.create_access_token({
                "sub": email,
                "user_id": new_user.user_id
            })

            # Return successful response with 200 status code
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "user_id": new_user.user_id,
                        "email": new_user.email,
                        "created_at": new_user.created_at.isoformat()
                    }
                }
            )
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user: {str(e)}"
            )


    async def login_user(self, email: str, password: str):
        try:
            # Retrieve the user from the database
            user = self.db.query(User).filter(User.email == email).first()

            if not user:
                # User not found
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )

            # Verify the password
            if not self.verify_password(password, user.password_hash):
                # Password mismatch
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )

            # Generate access token
            access_token = self.create_access_token({
                "sub": user.email,
                "user_id": user.user_id
            })

            # Return successful login response
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "user_id": user.user_id,
                        "email": user.email,
                        "created_at": user.created_at.isoformat()
                    },
                    "message": "Login successful"
                }
            )
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            # Catch unexpected errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}"
            )
