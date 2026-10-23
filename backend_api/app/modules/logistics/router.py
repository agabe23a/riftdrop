from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.websockets import manager
from app.modules.auth.models import User, UserRole
from app.modules.orders.models import Order, OrderState
from app.modules.logistics.fulfillment import FulfillmentService
from app.modules.stores.models import Store

router = APIRouter(prefix="/logistics", tags=["Real-Time Dispatch"])

# ==========================================
# 📡 WEBSOCKET ENDPOINTS
# ==========================================
@router.websocket("/ws/vendor/{store_id}")
async def vendor_websocket_endpoint(websocket: WebSocket, store_id: str):
    """React Web Dashboard connects here to listen for paid orders."""
    await manager.connect_vendor(websocket, store_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_vendor(websocket, store_id)

@router.websocket("/ws/rider")
async def rider_websocket_endpoint(websocket: WebSocket):
    """Rider Mobile App connects here to listen for 'Broadcast & Claim' jobs."""
    await manager.connect_rider(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_rider(websocket)


# ==========================================
# 🏍️ RIDER ACTIONS
# ==========================================
@router.post("/orders/{order_id}/accept")
async def accept_order(order_id: int, db: AsyncSession = Depends(get_db), current_vendor: User = Depends(require_role(UserRole.VENDOR))):
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    store = (await db.execute(select(Store).where(Store.id == order.store_id))).scalars().first()
    if not store or store.owner_id != current_vendor.id:
        raise HTTPException(status_code=403, detail="You do not own this order's store")
    if order.status != OrderState.PAID_IN_ESCROW:
        raise HTTPException(status_code=409, detail="Order cannot be accepted in its current state")
    order.status = OrderState.ACCEPTED_BY_VENDOR
    await db.commit()
    await manager.broadcast_to_riders({"event": "NEW_DELIVERY_AVAILABLE", "order_id": order.id, "payout": str(order.delivery_fee)})
    return {"message": "Order accepted and sent to riders"}

@router.post("/claim-order/{order_id}")
async def claim_order(
    order_id: int, 
    db: AsyncSession = Depends(get_db),
    current_rider: User = Depends(require_role(UserRole.RIDER))
):
    """The core of the 'Claim' protocol. The first rider to hit this gets the job."""
    
    # 1. Fetch the order but use a row-level lock (Requires PostgreSQL in production)
    # For now in SQLite, we check the state strictly.
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    # 2. Check if another rider already claimed it
    if order.status != OrderState.ACCEPTED_BY_VENDOR:
        raise HTTPException(status_code=400, detail="Too late! This order has already been claimed or is unavailable.")

    # 3. Lock the order to this specific rider
    order.rider_id = current_rider.id
    order.status = OrderState.RIDER_DISPATCHED
    await db.commit()

    return {"message": "Order claimed successfully! Proceed to the store for pickup."}

class PINVerification(BaseModel):
    pin: str

@router.post("/pickup-order/{order_id}")
async def pickup_order(
    order_id: int, 
    db: AsyncSession = Depends(get_db),
    current_rider: User = Depends(require_role(UserRole.RIDER))
):
    """Rider confirms they have picked up the items from the vendor."""
    result = await db.execute(select(Order).where(Order.id == order_id, Order.rider_id == current_rider.id))
    order = result.scalars().first()
    
    if not order or order.status != OrderState.RIDER_DISPATCHED:
        raise HTTPException(status_code=400, detail="Invalid order state for pickup.")
        
    order.status = OrderState.PICKED_UP
    await db.commit()
    
    return {"message": "Order marked as picked up. Proceed to customer location."}

@router.post("/complete-delivery/{order_id}")
async def complete_delivery(
    order_id: int, 
    pin_data: PINVerification,
    db: AsyncSession = Depends(get_db),
    current_rider: User = Depends(require_role(UserRole.RIDER))
):
    """Rider enters the customer's PIN to complete the loop and get paid."""
    return await FulfillmentService.confirm_delivery(
        db=db, 
        order_id=order_id, 
        rider_id=current_rider.id, 
        provided_pin=pin_data.pin
    )
