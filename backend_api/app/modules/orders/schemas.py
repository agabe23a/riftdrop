from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.modules.orders.models import OrderState

# --- INCOMING DATA (From the Frontend Cart) ---
class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CheckoutRequest(BaseModel):
    store_id: int
    delivery_lat: float
    delivery_lng: float
    items: List[CartItem]

class StoreInventoryCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="Master Product ID")
    price: float = Field(..., gt=0.0, description="Item price in KES")
    stock_quantity: int = Field(default=10, ge=0, description="Available inventory count")
    
# --- OUTGOING DATA (Response back to the App) ---
class PricingBreakdown(BaseModel):
    cart_total: float
    distance_km: float
    raw_delivery_fee: float
    discount_applied: float
    final_delivery_fee: float
    grand_total: float
    psychology_nudge: str

class OrderResponse(BaseModel):
    id: int
    store_id: int
    status: OrderState
    pricing: PricingBreakdown
    created_at: datetime

    class Config:
        from_attributes = True     