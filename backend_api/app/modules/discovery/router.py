import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.modules.catalog.models import MasterProduct
from app.modules.stores.models import Store, StoreInventory

router = APIRouter(prefix="/discovery", tags=["Customer Discovery"])

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def calculate_delivery_fee(distance_km: float) -> float:
    BASE_FARE = 30.0
    PER_KM_RATE = 15.0
    MINIMUM_FARE = 50.0
    return round(max(BASE_FARE + (distance_km * PER_KM_RATE), MINIMUM_FARE), 2)

@router.get("/search")
async def search_nearby_products(
    query: str = Query(..., min_length=2),
    user_lat: float = Query(...),
    user_lng: float = Query(...),
    max_distance_km: float = Query(5.0, gt=0, le=50),
    db: AsyncSession = Depends(get_db)
):
    # 1. Search Catalog
    catalog_query = select(MasterProduct).where(MasterProduct.name.ilike(f"%{query}%"))
    matched_products = (await db.execute(catalog_query)).scalars().all()
    
    if not matched_products:
        return {"results": [], "message": "No products found."}
        
    product_ids = [p.id for p in matched_products]
    
    # 2. Find Available Stock
    inventory_query = (
        select(StoreInventory)
        .options(selectinload(StoreInventory.store), selectinload(StoreInventory.product))
        .where(StoreInventory.product_id.in_(product_ids))
        .where(StoreInventory.stock_quantity > 0)
        .where(StoreInventory.is_available.is_(True))
    )
    available_stock = (await db.execute(inventory_query)).scalars().all()
    
    # 3. Process Distances and Financials
    results = []
    store_ids_found = set() # Keep track of which stores we found to grab upsells later
    
    for item in available_stock:
        store = item.store
        if not store.is_active:
            continue
            
        distance = calculate_distance_km(user_lat, user_lng, store.latitude, store.longitude)
        
        if distance <= max_distance_km:
            delivery_fee = calculate_delivery_fee(distance)
            store_ids_found.add(store.id)
            
            results.append({
                "inventory_id": item.id,
                "product_name": item.product.name,
                "store_name": store.name,
                "store_id": store.id,
                "distance_km": distance,
                "financials": {
                    "product_price": item.price,
                    "delivery_fee": delivery_fee,
                    "total_checkout_price": item.price + delivery_fee
                }
            })
            
    # 4. Sort by Best Value
    results.sort(key=lambda x: x["financials"]["total_checkout_price"])
    
    # Relevant complementary items are deterministic so customer results remain predictable.
    upsells = []
    if store_ids_found:
        upsell_query = (
            select(StoreInventory)
            .options(selectinload(StoreInventory.product))
            .where(StoreInventory.store_id.in_(store_ids_found))
            .where(StoreInventory.price <= 150.0) # CHEAP IMPULSE BUYS ONLY
            .where(StoreInventory.product_id.notin_(product_ids))
            .where(StoreInventory.stock_quantity > 0)
            .where(StoreInventory.is_available.is_(True))
            .order_by(StoreInventory.price.asc(), StoreInventory.id.asc())
            .limit(3)
        )
        potential_upsells = (await db.execute(upsell_query)).scalars().all()
        
        if potential_upsells:
            for u in potential_upsells:
                upsells.append({
                    "inventory_id": u.id,
                    "product_name": u.product.name,
                    "price": u.price,
                    "store_id": u.store_id,
                    "trigger_text": "Perfect with your order"
                })

    return {
        "search_term": query,
        "radius_km": max_distance_km,
        "results": results,
        "impulse_buys": upsells  # <-- The frontend will render these as small, tempting buttons
    }
