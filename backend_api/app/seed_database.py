import asyncio
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, Base 
from app.modules.auth.models import User, UserRole
from app.modules.stores.models import Store, StoreInventory
from app.modules.catalog.models import MasterProduct, Category

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def seed_data():
    print("🧹 Wiping the database clean...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("🏗️ Database rebuilt. Injecting Production Data...")
    
    async with AsyncSession(engine) as db:
        
        # 1. Create Users
        admin = User(
            email="ceo@riftdrop.com",
            phone_number="0700000001",
            hashed_password=hash_password("admin123"),
            full_name="Bomet Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        vendor = User(
            email="vendor@kmatt.com",
            phone_number="0700000002",
            hashed_password=hash_password("vendor123"),
            full_name="K-Matt Manager",
            role=UserRole.VENDOR,
            is_active=True,
            is_verified=True
        )
        
        rider = User(
            email="rider@riftdrop.com",
            phone_number="0700000003",
            hashed_password=hash_password("rider123"),
            full_name="Fast Bodaboda",
            role=UserRole.RIDER,
            is_active=True,
            is_verified=True
        )
        
        db.add_all([admin, vendor, rider])
        await db.flush() 
        print("✅ Users created (Admin, Vendor, Rider)")

        # 2. CREATE CATEGORY FIRST (So we can get its ID)
        category = Category(name="Food & Groceries")
        db.add(category)
        await db.flush()

        # 3. CREATE STORE USING THE CATEGORY ID
        store = Store(
            owner_id=vendor.id,
            name="K-Matt Supermarket",
            category_id=category.id, # <--- THE FIX: Using the integer ID!
            latitude=-0.7894,
            longitude=35.3281,
            is_active=True
        )
        db.add(store)
        await db.flush()
        
        # 4. Create Master Products
        soko = MasterProduct(
            name="Soko Maize Meal 2kg",
            category_id=category.id,
            image_url="https://via.placeholder.com/150",
            barcode="SOKO-001"
        )
        indomie = MasterProduct(
            name="Indomie Chicken Flavour",
            category_id=category.id,
            image_url="https://via.placeholder.com/150",
            barcode="INDO-002"
        )
        db.add_all([soko, indomie])

        query = """
        UPDATE master_products 
        SET name = 'foo';
        """

        # COMMIT EVERYTHING
        await db.commit() 
        
        print("✅ Store, Categories, and Master Catalog injected!")
        print("\n🎉 Seeding Complete. The system is ready.")

if __name__ == "__main__":
    asyncio.run(seed_data())