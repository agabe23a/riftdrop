from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MasterProductCreate(BaseModel):
    name: str
    category_id: int  # Ensure this is an ID to link properly in the database
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    base_description: Optional[str] = None 
    
# Brand new name to force a fresh compile
class CatalogCategory(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# Brand new name to force a fresh compile
class CatalogItemResponse(BaseModel):
    id: int
    name: str
    category_id: int
    
    # Strictly bound to the object above, impossible to be a string now
    category: CatalogCategory  
    
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    base_description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)