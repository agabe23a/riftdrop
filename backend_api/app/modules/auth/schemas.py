from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.modules.auth.models import UserRole

# Schemas for Data Coming IN (Requests)
class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., description="Phone number starting with country code, e.g., +254...")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)

# Schemas for Data Going OUT (Responses)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    phone_number: str
    full_name: str
    role: UserRole
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
