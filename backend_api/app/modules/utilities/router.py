from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.upload import upload_image_to_cloud
from app.modules.auth.models import User, UserRole, CustomerAddress
from app.modules.orders.models import Review, Order, OrderState

router = APIRouter(prefix="/utils", tags=["System Utilities"])

# --- 1. IMAGE UPLOADS ---
@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user) # Anyone logged in can upload
):
    """Uploads an image to Cloudinary and returns the URL for the frontend to use."""
    # Determine folder based on role
    folder = "riftdrop/stores" if current_user.role == UserRole.VENDOR else "riftdrop/products"
    secure_url = await upload_image_to_cloud(file, folder)
    return {"url": secure_url}

# --- 2. SAVED ADDRESSES ---
class AddressCreate(BaseModel):
    label: str
    address_details: str
    location_lat: float
    location_lng: float

@router.post("/addresses", status_code=status.HTTP_201_CREATED)
async def add_saved_address(
    address_in: AddressCreate,
    db: AsyncSession = Depends(get_db),
    current_customer: User = Depends(require_role(UserRole.CUSTOMER))
):
    """Saves a GPS pin so the user doesn't have to enter it again."""
    new_address = CustomerAddress(
        customer_id=current_customer.id,
        label=address_in.label,
        address_details=address_in.address_details,
        location_lat=address_in.location_lat,
        location_lng=address_in.location_lng
    )
    db.add(new_address)
    await db.commit()
    return {"message": "Address saved successfully."}

# --- 3. REVIEWS & TRUST ---
class ReviewCreate(BaseModel):
    store_rating: int
    rider_rating: int
    comment: str = None

@router.post("/reviews/{order_id}")
async def submit_review(
    order_id: int,
    review_in: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_customer: User = Depends(require_role(UserRole.CUSTOMER))
):
    """Submits a rating for the store and the rider after delivery."""
    result = await db.execute(select(Order).where(Order.id == order_id, Order.customer_id == current_customer.id))
    order = result.scalars().first()
    
    if not order or order.status != OrderState.DELIVERED:
        return {"error": "You can only review completed deliveries."}
        
    new_review = Review(
        order_id=order.id,
        customer_id=current_customer.id,
        store_id=order.store_id,
        rider_id=order.rider_id,
        store_rating=review_in.store_rating,
        rider_rating=review_in.rider_rating,
        comment=review_in.comment
    )
    db.add(new_review)
    await db.commit()
    return {"message": "Review submitted. Thank you for keeping RiftDrop safe!"}