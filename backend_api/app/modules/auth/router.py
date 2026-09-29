from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserLogin, Token, UserResponse, OTPVerifyRequest
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new user, store owner, or rider to the RiftDrop ecosystem."""
    return await AuthService.register_new_user(db, user_in)

@router.post("/login")
async def login(
    # Strictly enforces OAuth2 Form-Data standards
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """Authenticates a user and returns a JWT token. Complies with OAuth2."""
    
    # OAuth2 specifies the field MUST be called 'username', but we map it to our 'email'
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email via OTP first.")

    # Generate JWT
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_account(otp_request: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verifies a user's email via the 6-digit OTP code sent during registration."""
    return await AuthService.verify_otp(db, otp_request)