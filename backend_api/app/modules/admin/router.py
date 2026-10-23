from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import get_password_hash
from app.modules.auth.models import User, UserRole
from app.modules.catalog.models import Category
from app.modules.stores.models import Store

router = APIRouter(prefix="/admin", tags=["Administration"])


class StaffCreate(BaseModel):
    email: EmailStr
    phone_number: str = Field(pattern=r"^\+?\d{10,15}$")
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role: UserRole


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    parent_id: int | None = Field(default=None, gt=0)


async def require_super_admin(current_user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super administrator privileges are required")
    return current_user


@router.post("/staff", status_code=status.HTTP_201_CREATED)
async def create_staff(payload: StaffCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(require_super_admin)):
    if payload.role not in {UserRole.VENDOR, UserRole.RIDER, UserRole.ADMIN}:
        raise HTTPException(status_code=422, detail="Only operational accounts may be created here")
    if payload.role == UserRole.ADMIN and not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="Only a super administrator can create administrators")
    duplicate = (await db.execute(select(User.id).where((User.email == payload.email) | (User.phone_number == payload.phone_number)))).scalar_one_or_none()
    if duplicate:
        raise HTTPException(status_code=409, detail="Email or phone number is already in use")
    user = User(email=payload.email, phone_number=payload.phone_number, full_name=payload.full_name, hashed_password=get_password_hash(payload.password), role=payload.role, is_verified=True, is_active=True)
    db.add(user)
    await db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.patch("/users/{user_id}/active")
async def set_user_active(user_id: int, active: bool, db: AsyncSession = Depends(get_db), _: User = Depends(require_super_admin)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = active
    await db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_role(UserRole.ADMIN))):
    if payload.parent_id and not (await db.execute(select(Category.id).where(Category.id == payload.parent_id))).scalar_one_or_none():
        raise HTTPException(status_code=422, detail="Unknown parent category")
    category = Category(**payload.model_dump())
    db.add(category)
    await db.commit()
    return {"id": category.id, "name": category.name, "parent_id": category.parent_id}


@router.patch("/stores/{store_id}/active")
async def set_store_active(store_id: int, active: bool, db: AsyncSession = Depends(get_db), _: User = Depends(require_role(UserRole.ADMIN))):
    store = (await db.execute(select(Store).where(Store.id == store_id))).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    store.is_active = active
    await db.commit()
    return {"id": store.id, "is_active": store.is_active}
