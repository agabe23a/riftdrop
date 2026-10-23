from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import get_password_hash
from app.core.websockets import manager
from app.modules.auth.models import User, UserRole
from app.modules.orders.algorithms import LogisticsEngine
from app.modules.orders.models import EscrowLedger, Order, OrderItem, OrderState
from app.modules.orders.mpesa import MpesaService
from app.modules.orders.schemas import CheckoutRequest
from app.modules.stores.models import Store, StoreInventory

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def process_checkout( payload: CheckoutRequest, db: AsyncSession = Depends(get_db), customer: User = Depends(require_role(UserRole.CUSTOMER))):
    store = (await db.execute(select(Store).where(Store.id == payload.store_id, Store.is_active.is_(True)))).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=400, detail="This store is currently unavailable")
    item_ids = [item.inventory_id for item in payload.items]
    if len(set(item_ids)) != len(item_ids):
        raise HTTPException(status_code=422, detail="Cart contains duplicate inventory items")
    inventory = (await db.execute(select(StoreInventory).where(StoreInventory.id.in_(item_ids), StoreInventory.store_id == store.id, StoreInventory.is_available.is_(True)))).scalars().all()
    inventory_by_id = {item.id: item for item in inventory}
    if len(inventory_by_id) != len(item_ids):
        raise HTTPException(status_code=422, detail="Cart contains unavailable items")
    cart_total = Decimal("0.00")
    for requested in payload.items:
        item = inventory_by_id[requested.inventory_id]
        if item.stock_quantity < requested.quantity:
            raise HTTPException(status_code=409, detail="One or more items no longer have sufficient stock")
        cart_total += item.price * requested.quantity
    distance = Decimal(str(LogisticsEngine.calculate_haversine_distance(float(store.latitude), float(store.longitude), payload.delivery_lat, payload.delivery_lng)))
    pricing = LogisticsEngine.calculate_pricing_breakdown(float(cart_total), float(distance))
    delivery_fee = Decimal(str(pricing["final_delivery_fee"])).quantize(Decimal("0.01"))
    platform_fee = (cart_total * Decimal("0.05")).quantize(Decimal("0.01"))
    order = Order(customer_id=customer.id, store_id=store.id, cart_total=cart_total, delivery_fee=delivery_fee, platform_fee=platform_fee, grand_total=cart_total + delivery_fee, delivery_lat=payload.delivery_lat, delivery_lng=payload.delivery_lng, distance_km=distance, payment_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
    db.add(order)
    await db.flush()
    for requested in payload.items:
        item = inventory_by_id[requested.inventory_id]
        item.stock_quantity -= requested.quantity
        db.add(OrderItem(order_id=order.id, inventory_id=item.id, quantity=requested.quantity, price_at_checkout=item.price))
    db.add(EscrowLedger(order_id=order.id, held_amount=Decimal("0.00"), vendor_payout=cart_total-platform_fee, rider_payout=delivery_fee, platform_revenue=platform_fee))
    await db.commit()
    return {"order_id": order.id, "status": order.status, "total_to_pay": order.grand_total, "pricing": pricing}


@router.post("/{order_id}/pay")
async def initiate_payment(order_id: int, db: AsyncSession = Depends(get_db), customer: User = Depends(require_role(UserRole.CUSTOMER))):
    order = (await db.execute(select(Order).where(Order.id == order_id, Order.customer_id == customer.id))).scalar_one_or_none()
    if not order or order.status != OrderState.PENDING_PAYMENT or (order.payment_expires_at and order.payment_expires_at < datetime.now(timezone.utc)):
        raise HTTPException(status_code=409, detail="This order is no longer payable")
    response = await MpesaService.trigger_stk_push(customer.phone_number, order.grand_total, order.id)
    checkout_request_id = response.get("CheckoutRequestID")
    if not checkout_request_id:
        raise HTTPException(status_code=502, detail="Payment provider did not return a checkout reference")
    order.mpesa_checkout_request_id = checkout_request_id
    await db.commit()
    return {"message": "STK Push sent", "checkout_request_id": checkout_request_id}


@router.post("/mpesa-callback")
async def mpesa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    callback = data.get("Body", {}).get("stkCallback", {})
    reference = callback.get("CheckoutRequestID")
    if not reference:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    order = (await db.execute(select(Order).where(Order.mpesa_checkout_request_id == reference))).scalar_one_or_none()
    if not order or order.status != OrderState.PENDING_PAYMENT:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    if callback.get("ResultCode") != 0:
        order.status = OrderState.CANCELLED
        await db.commit()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    metadata = {entry.get("Name"): entry.get("Value") for entry in callback.get("CallbackMetadata", {}).get("Item", [])}
    receipt = metadata.get("MpesaReceiptNumber")
    if not receipt:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    order.status = OrderState.PAID_IN_ESCROW
    order.mpesa_receipt_number = str(receipt)
    order.delivery_pin_hash = get_password_hash(f"{secrets.randbelow(10000):04d}")
    ledger = (await db.execute(select(EscrowLedger).where(EscrowLedger.order_id == order.id))).scalar_one()
    ledger.held_amount = order.grand_total
    await db.commit()
    await manager.alert_vendor(str(order.store_id), {"event": "NEW_PAID_ORDER", "order_id": order.id, "cart_total": str(order.cart_total)})
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
