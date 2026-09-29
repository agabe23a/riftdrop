from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from typing import List
from pydantic import BaseModel
from jose import jwt

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.modules.auth.models import User, UserRole
from app.modules.stores.models import Store, StoreInventory
from app.modules.catalog.models import MasterProduct
from app.modules.stores.schemas import StoreCreate, InventoryAdd, StoreInventoryCreate, AggregatedSearchResponse, OfferDetail


router = APIRouter(prefix="/stores", tags=["Vendors & Search Engine Store Management"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# The Pydantic Security Guard for incoming GPS data
class StoreCreate(BaseModel):
    name: str
    category_id: int
    latitude: float
    longitude: float

# The Security Guard for incoming inventory data
class StoreInventoryCreate(BaseModel):
    master_product_id: int
    price: float
    stock_quantity: int    

# DEPENDENCY: Securely extract the real user ID from the JWT token
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_store(store_in: StoreCreate, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Creates a new physical store profile with GPS coordinates."""
    
    try:
        # NOTE: In a fully locked-down environment, we extract owner_id from the JWT token. 
        # For now, we assign it to owner_id = 1 to test the database pipeline.
        new_store = Store(
            name=store_in.name,
            category_id=store_in.category_id,
            latitude=store_in.latitude,
            longitude=store_in.longitude,
            owner_id=user_id
        )
        
        db.add(new_store)
        await db.commit()
        await db.refresh(new_store)
        
        return {
            "id": new_store.id,
            "name": new_store.name,
            "message": "Store successfully registered."
        }
    
    except Exception as e:
        await db.rollback()
        print(f"\n[CRITICAL DB ERROR] Store Creation Failed: {str(e)}\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database constraint failed. Check terminal for details."
        )
    
# ==========================================
# 🏪 VENDOR ROUTES (Secured)
# ==========================================
@router.post("/register-store", status_code=status.HTTP_201_CREATED)
async def register_store(
    store_in: StoreCreate, 
    db: AsyncSession = Depends(get_db),
    current_vendor: User = Depends(require_roles([UserRole.VENDOR]))
):
    """Allows a Vendor to register their physical shop."""
    new_store = Store(
        owner_id=current_vendor.id,
        name=store_in.name,
        category=store_in.category,
        location_lat=store_in.location_lat,
        location_lng=store_in.location_lng,
        is_active=True # In production, set this to False until Admin approves
    )
    db.add(new_store)
    await db.commit()
    await db.refresh(new_store)
    return new_store

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
 
# app/modules/stores/router.py

@router.get("/{store_id}/inventory")
async def get_store_inventory(store_id: int, db: AsyncSession = Depends(get_db)):
    """Fetches inventory joined with MasterProduct details (Name, Image URL)."""
    result = await db.execute(
        select(StoreInventory)
        .options(joinedload(StoreInventory.product)) # Loads master_product details (name, image_url)
        .where(StoreInventory.store_id == store_id)
    )
    return result.scalars().all()

# ==========================================
# 🔍 CUSTOMER AGGREGATION ENGINE (Public)
# ==========================================
@router.get("/search", response_model=List[AggregatedSearchResponse])
async def search_products(
    q: str = Query(..., min_length=2, description="Search term, e.g., 'Soko'"),
    db: AsyncSession = Depends(get_db)
):
    """
    THE USP: Searches the master catalog and returns all stores selling it, 
    automatically sorted by the cheapest price.
    """
    # 1. Complex JOIN query to grab Product, Inventory, and Store details at once
    result = await db.execute(
        select(MasterProduct, StoreInventory, Store)
        .join(StoreInventory, MasterProduct.id == StoreInventory.product_id)
        .join(Store, StoreInventory.store_id == Store.id)
        .where(MasterProduct.name.ilike(f"%{q}%"))
        .where(StoreInventory.is_available == True)
        .where(Store.is_active == True)
        .order_by(MasterProduct.id, StoreInventory.price.asc()) # Sort by cheapest first
    )
    
    rows = result.all()
    
    # 2. Restructure the flat SQL rows into our clean JSON Aggregator schema
    aggregation = {}
    for product, inventory, store in rows:
        if product.id not in aggregation:
            aggregation[product.id] = {
                "product_id": product.id,
                "product_name": product.name,
                "product_image": product.image_url,
                "best_price": inventory.price, # The first one is always cheapest due to SQL ordering
                "offers": []
            }
        
        aggregation[product.id]["offers"].append({
            "store_id": store.id,
            "store_name": store.name,
            "price": inventory.price,
            "stock_quantity": inventory.stock_quantity
        })

    return list(aggregation.values())

@router.post("/{store_id}/inventory", status_code=status.HTTP_201_CREATED)
async def add_product_to_store(
    store_id: int,
    inventory_in: StoreInventoryCreate,
    user_id: int = Depends(get_current_user_id), # Validates the JWT token
    db: AsyncSession = Depends(get_db)
):
    """Adds a master product to a specific store's inventory with a custom price."""
    
    # SECURITY CHECK: Does this user actually own this store?
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalars().first()
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")
    
    if store.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this store.")

    try:
        # Add the item to the shelves
        new_inventory = StoreInventory(
            store_id=store_id,
            master_product_id=inventory_in.master_product_id,
            price=inventory_in.price,
            stock_quantity=inventory_in.stock_quantity
        )
        
        db.add(new_inventory)
        await db.commit()
        
        return {"message": "Product successfully added to inventory."}
        
    except Exception as e:
        await db.rollback()
        print(f"\n[CRITICAL DB ERROR] Inventory Addition Failed: {str(e)}\n")
        raise HTTPException(
            status_code=500,
            detail="Failed to add product to database. Check terminal logs."
        )