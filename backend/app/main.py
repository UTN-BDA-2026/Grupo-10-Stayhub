import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError

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

# Configurar CORS de forma segura para permitir solo al frontend autorizado
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:5500",   # Para VS Code Live Server
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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


# ─── Exception Handlers Globales ────────────────────────────────────────────
# Capturan errores de DB que puedan escaparse de los routers individuales.
# Garantizan que el cliente siempre recibe un código HTTP semántico,
# nunca un 500 por una violación de constraint de la base de datos.

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """ForeignKeyViolation, UniqueViolation, CheckViolation → 400"""
    return JSONResponse(
        status_code=400,
        content={"detail": "Error de integridad en la base de datos. Verifique los datos enviados."},
    )


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    """Formato inválido (ej: geometría PostGIS mal formada) → 422"""
    return JSONResponse(
        status_code=422,
        content={"detail": "Formato de datos inválido. Verifique tipos y formatos (ej: coordenadas WKT)."},
    )


@app.get("/")
def root():
    return {"status": "ok", "proyecto": "StayHub"}


@app.get("/health")
def health():
    return {"status": "healthy"}
