import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# 1. CAMBIO DE SEGURIDAD: Usamos las credenciales de la API, no las del administrador
DATABASE_URL = (
    f"postgresql://{os.getenv('API_DB_USER')}:{os.getenv('API_DB_PASSWORD')}"
    f"@db:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    f"mongodb://mongo:{os.getenv('MONGO_PORT', 27017)}/{os.getenv('MONGO_DB', 'stayhub')}"
)

# 2. CAMBIO DE SEGURIDAD: Agregamos connect_args para gestionar el SSL/TLS
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args={"sslmode": "prefer"} 
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ... (Acá para abajo dejás todo el código de Mongo y get_db exactamente como estaba)

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
