from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..services.auth_service import AuthService
from ..models.auth import UserCreate, UserLogin, TokenResponse

router = APIRouter()

@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        print(f"Signup request for email: {user_data.email}")
        result = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password
        )
        print("Signup response:", result)
        return result
    except Exception as e:
        print(f"Signup exception: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        result = await auth_service.login_user(
            email=user_data.email,
            password=user_data.password
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )