from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.models import User, UserRole

# This tells FastAPI to look for the token in the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """Decrypts the JWT and retrieves the user from the database."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired or is invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            print("🚨 JWT ERROR: 'sub' (user_id) is missing from the token payload!")
            raise credentials_exception
            
    except jwt.ExpiredSignatureError as e:
        print(f"🚨 JWT EXPIRED: {str(e)}")
        raise credentials_exception
    except jwt.PyJWTError as e:
        print(f"🚨 JWT VERIFICATION FAILED: {str(e)}")
        raise credentials_exception
    except ValidationError as e:
        print(f"🚨 JWT VALIDATION ERROR: {str(e)}")
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    
    if user is None:
        print(f"🚨 DB ERROR: Token is valid, but User ID {user_id} does not exist in the database!")
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_active:
        print(f"🚨 SECURITY LOCK: User ID {user_id} exists but is inactive!")
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    return user

def require_role(required_role: UserRole):
    """A dependency generator that blocks users who do not have the required role."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Operation not permitted. Requires {required_role.value} privileges."
            )
        return current_user
    return role_checker


def require_roles(allowed_roles: list[UserRole]):
    """Allows multiple roles (e.g., ADMIN and VENDOR) to access an endpoint."""
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Operation not permitted for your security clearance."
            )
        return current_user
    return role_checker