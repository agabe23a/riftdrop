from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    RIDER = "RIDER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    # Role-Based Access Control (RBAC)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    
    # Safety and Security Flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Flips to true after OTP verification
    is_super_admin = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0, nullable=False)

class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    label = Column(String, nullable=False) # e.g., "Hostel Room 4", "Office"
    address_details = Column(String, nullable=False)
    
    # The exact coordinates to feed into our Haversine algorithm
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    
    is_default = Column(Boolean, default=False)   
