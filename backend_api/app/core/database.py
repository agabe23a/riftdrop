from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# The engine communicates with the database
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Prints SQL queries to the terminal for debugging
    future=True
)

# The session factory creates database sessions for each request
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# All our future database models will inherit from this Base
Base = declarative_base()

# Dependency to inject the database session into our routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session