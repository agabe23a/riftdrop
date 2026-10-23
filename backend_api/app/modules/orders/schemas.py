from typing import Annotated

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    inventory_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class CheckoutRequest(BaseModel):
    store_id: int = Field(gt=0)
    delivery_lat: float = Field(ge=-90, le=90)
    delivery_lng: float = Field(ge=-180, le=180)
    items: list[CartItem] = Field(min_length=1, max_length=50)
    phone_number: Annotated[str, Field(min_length=10, max_length=15, description="Customer's phone number for delivery updates")]
