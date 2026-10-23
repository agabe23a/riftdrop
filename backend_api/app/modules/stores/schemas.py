from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class StoreCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=160, description="Public name of the store")
    category_id: int = Field(..., gt=0)
    latitude: float = Field(..., ge=-90.0, le=90.0, description="GPS Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="GPS Longitude")

class StoreInventoryCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="ID referencing the Master Catalog")
    # Decimal prevents M-Pesa fraction errors. max_digits=12 handles up to 9,999,999,999.99 KES
    price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="Vendor's exact price")
    stock_quantity: int = Field(default=10, ge=0, le=1_000_000, description="Units on hand")
    is_available: bool = Field(default=True, description="Toggles customer visibility instantly")

class InventoryUpdate(BaseModel):
    # All fields are optional because a vendor might only want to update stock, not price
    price: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock_quantity: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    is_available: Optional[bool] = None
    image_url: Optional[str] = Field(default=None, max_length=500, description="S3 or Cloudinary URL for vendor-uploaded product photos")