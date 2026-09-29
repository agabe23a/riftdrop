from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.websockets import manager
from app.modules.auth.models import User, UserRole
from app.modules.stores.models import Store, StoreInventory
from app.modules.stores.schemas import StoreInventoryCreate
from app.modules.orders.models import Order, OrderItem, EscrowLedger, OrderState
from app.modules.orders.schemas import CheckoutRequest, OrderResponse 
from app.modules.orders.algorithms import LogisticsEngine
from app.modules.orders.mpesa import MpesaService 


router = APIRouter(prefix="/orders", tags=["Checkout & Logistics"])

@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def process_checkout(
    request: CheckoutRequest, 
    db: AsyncSession = Depends(get_db),
    current_customer: User = Depends(require_role(UserRole.CUSTOMER))
):
    """Processes a user's cart, calculates dynamic delivery, and initializes Escrow."""
    
    # 1. Verify the Store exists and is active
    store_result = await db.execute(select(Store).where(Store.id == request.store_id))
    store = store_result.scalars().first()
    if not store or not store.is_active:
        raise HTTPException(status_code=400, detail="This store is currently unavailable.")
        
    if not store.location_lat or not store.location_lng:
        raise HTTPException(status_code=400, detail="Store GPS coordinates missing. Cannot calculate delivery.")

    # 2. Verify Stock and Calculate Cart Total
    cart_total = 0.0
    valid_items = []
    
    for item in request.items:
        inv_result = await db.execute(
            select(StoreInventory).where(
                StoreInventory.store_id == request.store_id,
                StoreInventory.product_id == item.product_id,
                StoreInventory.is_available == True
            )
        )
        inventory = inv_result.scalars().first()
        
        if not inventory or inventory.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} is out of stock or requested quantity exceeds available stock.")
            
        cart_total += (inventory.price * item.quantity)
        valid_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "locked_price": inventory.price
        })

    # 3. Trigger the Logistics & Psychology Engine
    distance_km = LogisticsEngine.calculate_haversine_distance(
        lat1=store.location_lat, lon1=store.location_lng,
        lat2=request.delivery_lat, lon2=request.delivery_lng
    )
    pricing = LogisticsEngine.calculate_pricing_breakdown(cart_total, distance_km)

    # 4. Create the Order (State: PENDING_PAYMENT)
    platform_cut = cart_total * 0.05 # RiftDrop takes 5% of the cart value
    
    new_order = Order(
        customer_id=current_customer.id,
        store_id=request.store_id,
        cart_total=cart_total,
        delivery_fee=pricing["final_delivery_fee"],
        platform_fee=platform_cut,
        grand_total=pricing["total_checkout_price"],
        delivery_lat=request.delivery_lat,
        delivery_lng=request.delivery_lng,
        distance_km=pricing["distance_km"],
        status=OrderState.PENDING_PAYMENT
    )
    db.add(new_order)
    await db.flush() # Flushes to DB to get the new_order.id without fully committing yet

    # 5. Lock in the Order Items
    for v_item in valid_items:
        new_order_item = OrderItem(
            order_id=new_order.id,
            product_id=v_item["product_id"],
            quantity=v_item["quantity"],
            price_at_checkout=v_item["locked_price"]
        )
        db.add(new_order_item)

    # 6. Initialize the Double-Entry Escrow Ledger
    # The money isn't here yet, but the ledger expects it upon M-Pesa completion
    vendor_takehome = cart_total - platform_cut
    
    new_ledger = EscrowLedger(
        order_id=new_order.id,
        held_amount=0.0, # Will update to grand_total when M-Pesa is successful
        vendor_payout=vendor_takehome,
        rider_payout=pricing["final_delivery_fee"],
        platform_revenue=platform_cut,
        is_released=False
    )
    db.add(new_ledger)
    
    # Commit the entire transaction atomically
    await db.commit()
    await db.refresh(new_order)

    # 7. Return formatted payload to the frontend
    return {
        "id": new_order.id,
        "store_id": new_order.store_id,
        "status": new_order.status,
        "pricing": pricing,
        "created_at": new_order.created_at
    }

@router.post("/checkout")
async def process_checkout(checkout_in: CheckoutSchema, user_id: int = Depends(get_current_user)):
    """
    MILLION DOLLAR LOGIC:
    1. Check if other orders for the same store exist within a 15-minute window.
    2. If yes, dynamically reduce the delivery fee for this user.
    3. Group these orders in the database for the rider's batch-delivery interface.
    """
    
    # 1. Look for 'Pending' orders at the same store
    # 2. If 'bundling_eligible' is True:
    #    delivery_fee = delivery_fee * 0.4  (40% of the cost)
    
    # 3. Save order to DB with 'is_bundled: True'
    return {"message": "Order placed", "delivery_discount": "Applied"}

@router.post("/{order_id}/pay", status_code=status.HTTP_200_OK)
async def initiate_payment(
    order_id: int, 
    db: AsyncSession = Depends(get_db),
    current_customer: User = Depends(require_role(UserRole.CUSTOMER))
):
    """Customer triggers the M-Pesa prompt on their phone."""
    result = await db.execute(select(Order).where(Order.id == order_id, Order.customer_id == current_customer.id))
    order = result.scalars().first()
    
    if not order or order.status != OrderState.PENDING_PAYMENT:
        raise HTTPException(status_code=400, detail="Invalid order or order is already paid.")

    # Call Safaricom API
    mpesa_response = await MpesaService.trigger_stk_push(
        phone_number=current_customer.phone_number,
        amount=order.grand_total,
        order_id=order.id
    )
    
    return {"message": "STK Push sent. Please check your phone.", "provider_response": mpesa_response}


@router.post("/mpesa-callback")
async def mpesa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Safaricom hits this endpoint to tell us if the payment succeeded."""
    data = await request.json()
    
    # Safaricom nests the data deeply in their JSON structure
    stk_callback = data.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    
    # We can extract the Order ID from the checkout payload we sent earlier, 
    # but for safety, we often map the CheckoutRequestID in production.
    # We'll mock the extraction here for structural purposes.
    
    if result_code == 0:
        # Payment was successful!
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        receipt_number = next((item["Value"] for item in callback_metadata if item["Name"] == "MpesaReceiptNumber"), None)
        
        # IN PRODUCTION: You would find the exact Order by matching the CheckoutRequestID
        # and update the Escrow Ledger:
        # order.status = OrderState.PAID_IN_ESCROW
        # order.mpesa_receipt_number = receipt_number
        # escrow_ledger.held_amount = order.grand_total
        # await db.commit()
        # 1. Ping the Vendor Dashboard to start packing
        await manager.alert_vendor(
            store_id=str(order.store_id), 
            message={"event": "NEW_PAID_ORDER", "order_id": order.id, "cart_total": order.cart_total}
        )
        
        # 2. Broadcast to all Bomet Riders to start the claim race
        await manager.broadcast_to_riders(
            message={"event": "NEW_DELIVERY_AVAILABLE", "order_id": order.id, "payout": order.delivery_fee}
        )
        
        print(f"💰 SUCCESS! M-Pesa Receipt: {receipt_number} | Broadcasts Fired!")

        print(f"💰 SUCCESS! M-Pesa Receipt: {receipt_number}")
    else:
        # Payment Failed or Cancelled by User
        error_desc = stk_callback.get("ResultDesc")
        print(f"❌ M-PESA FAILED: {error_desc}")

    # You must always return a fast 200 OK to Safaricom, otherwise they will keep retrying
    return {"ResultCode": 0, "ResultDesc": "Accepted"}