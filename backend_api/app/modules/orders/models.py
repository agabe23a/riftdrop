import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    cart_total = Column(Numeric(12, 2), nullable=False)
    delivery_fee = Column(Numeric(12, 2), nullable=False)
    platform_fee = Column(Numeric(12, 2), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)
    delivery_lat = Column(Numeric(9, 6), nullable=False)
    delivery_lng = Column(Numeric(9, 6), nullable=False)
    distance_km = Column(Numeric(8, 2), nullable=False)
    status = Column(Enum(OrderState), default=OrderState.PENDING_PAYMENT, nullable=False, index=True)
    mpesa_receipt_number = Column(String(64), unique=True, nullable=True)
    mpesa_checkout_request_id = Column(String(128), unique=True, nullable=True, index=True)
    delivery_pin_hash = Column(String(128), nullable=True)
    payment_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey("store_inventory.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_checkout = Column(Numeric(12, 2), nullable=False)
    order = relationship("Order", back_populates="items")


class EscrowLedger(Base):
    __tablename__ = "escrow_ledger"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    held_amount = Column(Numeric(12, 2), nullable=False)
    vendor_payout = Column(Numeric(12, 2), nullable=False)
    rider_payout = Column(Numeric(12, 2), nullable=False)
    platform_revenue = Column(Numeric(12, 2), nullable=False)
    is_released = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False)
    store_rating = Column(Integer, nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rider_rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
