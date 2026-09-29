from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Self-referential foreign key for Parent -> Child hierarchy
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    subcategories = relationship("Category", backref="parent", remote_side=[id])
    products = relationship("MasterProduct", back_populates="category")


class MasterProduct(Base):
    __tablename__ = "master_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False) 
    
    # NEW: Strictly linked to the Category table
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    image_url = Column(String, nullable=True)
    barcode = Column(String, unique=True, index=True, nullable=True)
    base_description = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")