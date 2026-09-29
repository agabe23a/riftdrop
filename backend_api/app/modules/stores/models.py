from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, index=True, nullable=False) 
    
    # --- CHANGED: Now links to the official Category table ---
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False) 
    # --------------------------------------------------------
    
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    inventory = relationship("StoreInventory", back_populates="store")

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class StoreInventory(Base):
    """The junction table linking a Store to a MasterProduct with a specific price."""
    __tablename__ = "store_inventory"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("master_products.id", ondelete="CASCADE"), nullable=False)
    
    # The specific price this store is charging
    price = Column(Float, nullable=False) 
    stock_quantity = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Establish bidirectional relationship
    store = relationship("Store", back_populates="inventory")