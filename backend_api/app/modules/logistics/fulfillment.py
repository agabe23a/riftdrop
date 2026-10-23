from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from datetime import datetime, timezone

from app.modules.orders.models import Order, EscrowLedger, OrderState
from app.core.security import verify_password

class FulfillmentService:
    @staticmethod
    async def confirm_delivery(db: AsyncSession, order_id: int, rider_id: int, provided_pin: str):
        """Verifies the PIN and triggers the Escrow release."""
        
        # 1. Fetch Order and Escrow Ledger
        result = await db.execute(select(Order).where(Order.id == order_id, Order.rider_id == rider_id))
        order = result.scalars().first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or not assigned to you.")
            
        if order.status != OrderState.PICKED_UP:
            raise HTTPException(status_code=400, detail="Order is not in a valid state for delivery.")
            
        # 2. Verify the PIN
        if not order.delivery_pin_hash or not verify_password(provided_pin, order.delivery_pin_hash):
            raise HTTPException(status_code=401, detail="Incorrect Delivery PIN. Do not hand over the goods.")
            
        # 3. Fetch the Escrow Ledger
        escrow_result = await db.execute(select(EscrowLedger).where(EscrowLedger.order_id == order.id))
        escrow = escrow_result.scalars().first()
        
        if not escrow or escrow.is_released:
            raise HTTPException(status_code=400, detail="Escrow anomaly detected. Contact Support.")

        # 4. Execute the State Change & Ledger Release
        order.status = OrderState.DELIVERED
        
        escrow.is_released = True
        escrow.released_at = datetime.now(timezone.utc)
        
        # IN PRODUCTION: Here you would trigger an API call to a payout provider 
        # (like M-Pesa B2C) to physically send the `escrow.vendor_payout` to the Store 
        # and the `escrow.rider_payout` to the Rider's wallet.
        
        await db.commit()
        return {"message": "Delivery Confirmed! Escrow funds have been released to your wallet."}
