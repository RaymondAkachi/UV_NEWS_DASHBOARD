from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
# import asyncio
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
# print(DATABASE_URL)
# Create an asynchronous engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for verbose SQL logging (useful for debugging)
    pool_size=10,  # Number of connections to keep in the pool
    max_overflow=5,  # Number of connections that can be opened beyond pool_size
    pool_timeout=30,  # seconds to wait for a connection from the pool
    connect_args={
        "timeout": 10  # Connection timeout for asyncpg (in seconds)
    }
)

# Declarative base for defining models
Base = declarative_base()

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents objects from expiring after commit
)


# engine = create_async_engine(DATABASE_URL)

# # Declarative base for defining models
# Base = declarative_base()

# AsyncSessionLocal = sessionmaker(
#     bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session


def init_db():
    Base.metadata.create_all(bind=engine)
