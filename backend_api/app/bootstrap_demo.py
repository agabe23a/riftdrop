"""Create local-only, non-production demo accounts without deleting data."""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.modules.auth.models import User, UserRole

ACCOUNTS = (
    ("admin@riftdrop.local", "0700000100", "RiftDrop Super Admin", UserRole.ADMIN, True, "ChangeMe-Admin-2026"),
    ("vendor@riftdrop.local", "0700000101", "RiftDrop Demo Vendor", UserRole.VENDOR, False, "ChangeMe-Vendor-2026"),
)

async def main():
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Demo accounts cannot be created in production")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        for email, phone, name, role, super_admin, password in ACCOUNTS:
            if not (await db.execute(select(User.id).where(User.email == email))).scalar_one_or_none():
                db.add(User(email=email, phone_number=phone, full_name=name, hashed_password=get_password_hash(password), role=role, is_verified=True, is_super_admin=super_admin))
        await db.commit()
    print("Local demo accounts are ready. Change these passwords before any shared deployment.")

if __name__ == "__main__":
    asyncio.run(main())
