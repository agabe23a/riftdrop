from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StoreInventoryCreate(BaseModel):
    product_id: int
    price: float
    stock_quantity: int = 10
    is_available: bool = True

# --- VENDOR SCHEMAS (Data Coming In) ---
class StoreCreate(BaseModel):
    name: str
    category: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class InventoryAdd(BaseModel):
    product_id: int
    price: float
    stock_quantity: int = 10

# --- SEARCH AGGREGATOR SCHEMAS (Data Going Out to Customer) ---
class OfferDetail(BaseModel):
    store_id: int
    store_name: str
    price: float
    stock_quantity: int

class AggregatedSearchResponse(BaseModel):
    product_id: int
    product_name: str
    product_image: Optional[str]
    best_price: float
    offers: List[OfferDetail] # Ordered from cheapest to most expensive