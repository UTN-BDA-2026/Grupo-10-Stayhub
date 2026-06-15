import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@db:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    f"mongodb://mongo:{os.getenv('MONGO_PORT', 27017)}/{os.getenv('MONGO_DB', 'stayhub')}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB async client
mongo_client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo():
    global mongo_client, mongo_db
    mongo_client = AsyncIOMotorClient(MONGODB_URL)
    mongo_db = mongo_client[os.getenv("MONGO_DB", "stayhub")]
    print("✓ Conectado a MongoDB")


async def close_mongo():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("✓ Conexión a MongoDB cerrada")


def get_mongo_db() -> AsyncIOMotorDatabase:
    if mongo_db is None:
        raise RuntimeError("MongoDB no está inicializado")
    return mongo_db


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
