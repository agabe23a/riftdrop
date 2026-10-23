import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.modules.auth.models import User, OTPVerification, UserRole
from app.modules.auth.schemas import UserCreate, OTPVerifyRequest
from app.core.security import get_password_hash, verify_password
from app.core.notifications import send_email

class AuthService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_phone(db: AsyncSession, phone_number: str) -> User | None:
        result = await db.execute(select(User).where(User.phone_number == phone_number))
        return result.scalars().first()

    @staticmethod
    async def generate_otp_for_email(db: AsyncSession, email: str) -> str:
        """Generates a 6-digit OTP and saves it to the database."""
        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        db_otp = OTPVerification(
            email=email,
            otp_code=get_password_hash(otp_code),
            expires_at=expires_at
        )
        db.add(db_otp)
        await db.commit()
        await send_email(email, "Verify your RiftDrop account", f"Your RiftDrop verification code is {otp_code}. It expires in 10 minutes.")
        
        return otp_code

    @staticmethod
    async def register_new_user(db: AsyncSession, user_in: UserCreate) -> User:
        if await AuthService.get_user_by_email(db, user_in.email):
            raise HTTPException(status_code=400, detail="Email already registered.")
        if await AuthService.get_user_by_phone(db, user_in.phone_number):
            raise HTTPException(status_code=400, detail="Phone number already registered.")

        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            phone_number=user_in.phone_number,
            hashed_password=hashed_pwd,
            full_name=user_in.full_name,
            role=UserRole.CUSTOMER,
            is_verified=False 
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Trigger OTP Generation upon successful registration
        await AuthService.generate_otp_for_email(db, db_user.email)
        
        return db_user

    @staticmethod
    async def verify_otp(db: AsyncSession, otp_request: OTPVerifyRequest) -> dict:
        """Validates the OTP and activates the user account."""
        # Find the latest unused OTP for this email
        result = await db.execute(
            select(OTPVerification)
            .where(
                OTPVerification.email == otp_request.email,
                OTPVerification.is_used == False
            )
            .order_by(OTPVerification.id.desc())
        )
        otp_record = result.scalars().first()

        if not otp_record or otp_record.attempts >= 5:
            raise HTTPException(status_code=400, detail="Invalid OTP code.")
            
        # Ensure it is timezone-aware before comparing
        current_time = datetime.now(timezone.utc)
        # SQLite sometimes drops timezone info, so we force it to UTC for safe comparison
        if otp_record.expires_at.replace(tzinfo=timezone.utc) < current_time:
            raise HTTPException(status_code=400, detail="OTP code has expired.")
        otp_record.attempts += 1
        if not verify_password(otp_request.otp_code, otp_record.otp_code):
            await db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP code.")

        # Mark OTP as used
        otp_record.is_used = True
        
        # Verify the User
        user = await AuthService.get_user_by_email(db, otp_request.email)
        if user:
            user.is_verified = True

        await db.commit()
        return {"message": "Account successfully verified."}

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        user = await AuthService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        
        # Security Block: Prevent login if not verified
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Account not verified. Please complete OTP verification.")
            
        return user
