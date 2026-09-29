from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.catalog.models import Category

# Your exact Bomet County Market Structure
TAXONOMY = {
    "Grocery & Food": ["Fruits", "Vegetables", "Meat", "Seafood", "Dairy", "Bakery", "Frozen Foods", "Rice", "Flour", "Cooking Oil", "Snacks", "Beverages"],
    "Electronics": ["Smartphones", "Laptops", "Tablets", "TVs", "Audio", "Gaming", "Smart Home", "Computer Accessories", "Phone Accessories", "Networking"],
    "Fashion": ["Men's Clothing", "Women's Clothing", "Kids Clothing", "Shoes", "Bags", "Watches", "Jewelry"],
    "Home & Living": ["Furniture", "Kitchenware", "Bedding", "Lighting", "Home Decor", "Storage"],
    "Health & Pharmacy": ["Medicines", "Vitamins", "First Aid", "Medical Devices", "Personal Hygiene"],
    "Beauty & Personal Care": ["Skincare", "Haircare", "Makeup", "Fragrances", "Grooming"],
    "Baby & Kids": ["Diapers", "Baby Food", "Baby Clothing", "Toys", "Baby Care"],
    "Sports & Outdoors": ["Gym Equipment", "Football", "Cycling", "Camping", "Fitness Accessories"],
    "Automotive": ["Car Accessories", "Engine Oil", "Tyres", "Batteries", "Car Care"],
    "Pet Supplies": ["Dog Food", "Cat Food", "Pet Toys", "Pet Care"],
    "Office & Stationery": ["Books", "Pens", "Paper", "Printers", "Office Supplies"],
    "Flowers & Gifts": ["Flowers", "Cakes", "Gift Hampers", "Greeting Cards"],
    "Services": ["Laundry", "Cleaning", "Repairs", "Printing", "Other Local Services"]
}

async def seed_categories(db: AsyncSession):
    """Checks if categories exist, and if not, injects the master taxonomy."""
    # Check if we already have categories to prevent duplicates
    result = await db.execute(select(Category).limit(1))
    if result.scalars().first():
        print("✅ Taxonomy already seeded. Skipping.")
        return

    print("🌱 Seeding RiftDrop Master Taxonomy...")
    
    for parent_name, children in TAXONOMY.items():
        # Create Parent
        parent_cat = Category(name=parent_name, parent_id=None)
        db.add(parent_cat)
        await db.flush() # Flush to get the parent_cat.id immediately
        
        # Create Children
        for child_name in children:
            child_cat = Category(name=child_name, parent_id=parent_cat.id)
            db.add(child_cat)
            
    await db.commit()
    print("🌳 RiftDrop Taxonomy successfully planted in the database!")