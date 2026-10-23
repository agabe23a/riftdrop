from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class MasterProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category_id: int = Field(gt=0)
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
