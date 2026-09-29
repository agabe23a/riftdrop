from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class OrderState(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID_IN_ESCROW = "PAID_IN_ESCROW"
    ACCEPTED_BY_VENDOR = "ACCEPTED_BY_VENDOR"
    RIDER_DISPATCHED = "RIDER_DISPATCHED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Assigned later
    
    # Financials
    cart_total = Column(Float, nullable=False)
    delivery_fee = Column(Float, nullable=False)
    platform_fee = Column(Float, default=0.0) # Our cut
    grand_total = Column(Float, nullable=False)
    
    # Logistics
    delivery_lat = Column(Float, nullable=False)
    delivery_lng = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    
    # State Machine
    status = Column(Enum(OrderState), default=OrderState.PENDING_PAYMENT, nullable=False)
    mpesa_receipt_number = Column(String, unique=True, nullable=True)
    delivery_pin = Column(String(4), nullable=True) # Generated upon successful M-Pesa payment

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    inventory_id = Column(Integer, ForeignKey("store_inventory.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    price_at_checkout = Column(Float, nullable=False) # Locks the price so vendor changes don't affect old orders
    
    order = relationship("Order", back_populates="items")

class EscrowLedger(Base):
    """The Double-Entry Trust System."""
    __tablename__ = "escrow_ledger"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Where the money is
    held_amount = Column(Float, nullable=False)
    vendor_payout = Column(Float, nullable=False)
    rider_payout = Column(Float, nullable=False)
    platform_revenue = Column(Float, nullable=False)
    
    is_released = Column(Boolean, default=False) 
    # Flips to True ONLY when order is DELIVERED
    released_at = Column(DateTime(timezone=True), nullable=True)


class Review(Base):
    """The Trust Engine: Keeps Vendors and Riders accountable."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Customer rates the Store (1-5)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_rating = Column(Integer, nullable=False) 
    
    # Customer rates the Rider (1-5)
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rider_rating = Column(Integer, nullable=False)
    
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())    