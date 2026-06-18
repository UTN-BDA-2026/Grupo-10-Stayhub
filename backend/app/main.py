from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import close_mongo, connect_to_mongo
from app.routers.logs import router as logs_router
from app.routers.propiedades import router as propiedades_router
from app.routers.reservas import router as reservas_router
from app.routers.reseñas import router as reseñas_router
from app.routers.usuarios import router as usuarios_router

app = FastAPI(
    title="StayHub API",
    description="Plataforma de gestión de alojamientos — UTN Base de Datos Avanzada",
    version="0.1.0",
)

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo()


app.include_router(usuarios_router)
app.include_router(propiedades_router)
app.include_router(reservas_router)
app.include_router(reseñas_router)
app.include_router(logs_router)


@app.get("/")
def root():
    return {"status": "ok", "proyecto": "StayHub"}


@app.get("/health")
def health():
    return {"status": "healthy"}
