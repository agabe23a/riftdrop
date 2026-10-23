from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.modules.auth.models import User, UserRole
from app.modules.catalog.models import Category, MasterProduct
from app.modules.stores.models import Store, StoreInventory
from app.modules.stores.schemas import InventoryUpdate, StoreCreate, StoreInventoryCreate

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_store(payload: StoreCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles([UserRole.VENDOR, UserRole.ADMIN]))):
    if not (await db.execute(select(Category.id).where(Category.id == payload.category_id))).scalar_one_or_none():
        raise HTTPException(status_code=422, detail="Unknown category")
    store = Store(owner_id=current_user.id, **payload.model_dump())
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return {"id": store.id, "name": store.name, "is_active": store.is_active}


async def get_owned_store(store_id: int, db: AsyncSession, current_user: User) -> Store:
    store = (await db.execute(select(Store).where(Store.id == store_id))).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if current_user.role != UserRole.ADMIN and store.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this store")
    return store


@router.get("/{store_id}/inventory")
async def list_inventory(store_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await get_owned_store(store_id, db, current_user)
    inventory = (await db.execute(select(StoreInventory).options(selectinload(StoreInventory.product)).where(StoreInventory.store_id == store_id))).scalars().all()
    return [{"id": item.id, "product_id": item.product_id, "name": item.product.name, "image_url": item.image_url or item.product.image_url, "price": item.price, "stock_quantity": item.stock_quantity, "is_available": item.is_available} for item in inventory]

@router.get("/{store_id}/inventory")
async def get_store_inventory(store_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StoreInventory)
        .options(joinedload(StoreInventory.product)) # Loads master_product details (name, image_url)
        .where(StoreInventory.store_id == store_id)
    )
    return result.scalars().all()

@router.post("/{store_id}/inventory", status_code=status.HTTP_201_CREATED)
async def add_product_to_store(
    store_id: int,
    payload: StoreInventoryCreate, # Ensure this matches your Pydantic schema
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.VENDOR, UserRole.ADMIN]))
):
    """Adds a product to a store. Allows Admins to bypass the ownership check."""
    
    # 1. Look up the store
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalars().first()
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    # 2. THE ADMIN OVERRIDE LOGIC
    # If you are NOT an admin, and you DO NOT own the store, kick you out.
    if current_user.role != UserRole.ADMIN and store.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cross-tenant breach: You do not own this store.")

    # 3. Save to Database
    try:
        new_inventory = StoreInventory(
            store_id=store_id,
            product_id=payload.product_id, 
            price=payload.price,
            stock_quantity=payload.stock_quantity,
            is_available=True
        )
        
        db.add(new_inventory)
        await db.commit()
        return {"message": "Product successfully added to inventory!"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error. Check terminal.")


@router.patch("/{store_id}/inventory/{inventory_id}")
async def update_inventory(store_id: int, inventory_id: int, payload: InventoryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await get_owned_store(store_id, db, current_user)
    item = (await db.execute(select(StoreInventory).where(StoreInventory.id == inventory_id, StoreInventory.store_id == store_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.commit()
    return {"message": "Inventory updated"}
