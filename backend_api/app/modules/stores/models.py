from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(160), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    inventory = relationship("StoreInventory", back_populates="store", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_store_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_store_longitude"),
    )


class StoreInventory(Base):
    __tablename__ = "store_inventory"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("master_products.id", ondelete="RESTRICT"), nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    image_url = Column(String(500), nullable=True)

    store = relationship("Store", back_populates="inventory")
    product = relationship("MasterProduct")

    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_store_inventory_product"),
        CheckConstraint("price >= 0", name="ck_inventory_price"),
        CheckConstraint("stock_quantity >= 0", name="ck_inventory_stock"),
    )
