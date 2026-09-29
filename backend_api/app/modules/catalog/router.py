from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import selectinload 

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.modules.auth.models import User, UserRole
from app.modules.catalog.models import MasterProduct
from app.modules.catalog.schemas import CatalogItemResponse, MasterProductCreate

# --- SCHEMAS ---
class MasterProductCreate(BaseModel):
    name: str
    category: str
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    base_description: Optional[str] = None

class MasterProductResponse(MasterProductCreate):
    id: int

    class Config:
        from_attributes = True

# --- ROUTER ---
router = APIRouter(prefix="/catalog", tags=["Master Catalog"])

@router.post("/", response_model=MasterProductResponse, status_code=status.HTTP_201_CREATED)
async def create_master_product(
    product_in: MasterProductCreate,
    db: AsyncSession = Depends(get_db),
    # THIS LINE ENFORCES SECURITY: Only ADMINs can hit this endpoint
    current_admin: User = Depends(require_role(UserRole.ADMIN)) 
):
    """Creates a universal Master Product (Super Admin Only)."""
    # Check if barcode already exists
    if product_in.barcode:
        result = await db.execute(select(MasterProduct).where(MasterProduct.barcode == product_in.barcode))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Product with this barcode already exists.")

    new_product = MasterProduct(**product_in.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.get("/")
async def get_all_master_products(db: AsyncSession = Depends(get_db)):
    """Public route: Anyone can view the master catalog."""

    result = await db.execute(
        select(MasterProduct).options(selectinload(MasterProduct.category))
    )
    products = result.scalars().all()
    
    # BULLETPROOF SERIALIZATION
    # We manually map the DB object to a clean dictionary. 
    # This completely bypasses Pydantic's strict object validation errors.
    return [
        {
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            # We explicitly extract the string name here so Pydantic doesn't panic
            "category": p.category.name if p.category else "Uncategorized", 
            "image_url": p.image_url,
            "barcode": p.barcode,
            "base_description": p.base_description,
            "created_at": p.created_at
        }
        for p in products
    ]