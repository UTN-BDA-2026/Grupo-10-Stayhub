from fastapi import FastAPI

from app.routers.propiedades import router as propiedades_router
from app.routers.reservas import router as reservas_router
from app.routers.usuarios import router as usuarios_router

app = FastAPI(
    title="StayHub API",
    description="Plataforma de gestión de alojamientos — UTN Base de Datos Avanzada",
    version="0.1.0",
)

app.include_router(usuarios_router)
app.include_router(propiedades_router)
app.include_router(reservas_router)


@app.get("/")
def root():
    return {"status": "ok", "proyecto": "StayHub"}


@app.get("/health")
def health():
    return {"status": "healthy"}
