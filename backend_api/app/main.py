from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal 
from app.core.seeder import seed_categories 
from app.modules.auth.models import User, OTPVerification, CustomerAddress 
from app.modules.auth.router import router as auth_router
from app.modules.catalog.models import MasterProduct
from app.modules.catalog.router import router as catalog_router
from app.modules.stores.models import Store, StoreInventory
from app.modules.stores.router import router as stores_router
from app.modules.orders.models import Order, OrderItem, EscrowLedger, Review 
from app.modules.orders.router import router as orders_router 
from app.modules.logistics.router import router as logistics_router
from app.modules.utilities.router import router as utils_router
from app.modules.discovery.router import router as discovery_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173", 
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174"
        ],
            
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            await seed_categories(db)

    # --- Mount Domain Modules ---
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(catalog_router, prefix=settings.API_V1_STR)
    app.include_router(stores_router, prefix=settings.API_V1_STR)
    app.include_router(orders_router, prefix=settings.API_V1_STR)
    app.include_router(logistics_router, prefix=settings.API_V1_STR)
    app.include_router(utils_router, prefix=settings.API_V1_STR)
    app.include_router(stores_router, prefix=settings.API_V1_STR)
    app.include_router(discovery_router, prefix=settings.API_V1_STR)

    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "online",
            "project": settings.PROJECT_NAME,
            "message": "RiftDrop core database mapping and security engines active."
        }

    return app

app = create_app()