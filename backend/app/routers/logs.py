from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_mongo_db
from app.repositories.log_actividad import LogActividadRepository
from app.schemas.log_actividad import LogActividad, LogActividadCreate

router = APIRouter(prefix="/logs", tags=["Logs de Actividad"])


def get_log_repository(db: AsyncIOMotorDatabase = Depends(get_mongo_db)) -> LogActividadRepository:
    return LogActividadRepository(db)


@router.post("/", response_model=dict)
async def crear_log(
    log: LogActividadCreate,
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Crear un nuevo log de actividad"""
    log_id = await repo.crear(log)
    return {"id": log_id, "mensaje": "Log creado exitosamente"}


@router.get("/{log_id}", response_model=dict)
async def obtener_log(
    log_id: str,
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Obtener un log por su ID"""
    log = await repo.obtener_por_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log no encontrado")
    log["id"] = str(log["_id"])
    return log


@router.get("/usuario/{usuario_id}")
async def obtener_logs_usuario(
    usuario_id: int,
    limite: int = Query(100, le=1000),
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Obtener logs de un usuario específico"""
    logs = await repo.obtener_por_usuario(usuario_id, limite)
    return logs


@router.get("/tabla/{tabla}")
async def obtener_logs_tabla(
    tabla: str,
    limite: int = Query(100, le=1000),
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Obtener logs de una tabla específica"""
    logs = await repo.obtener_por_tabla(tabla, limite)
    return logs


@router.get("/")
async def listar_logs(
    limite: int = Query(100, le=1000),
    pagina: int = Query(1, ge=1),
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Listar todos los logs con paginación"""
    logs = await repo.obtener_todos(limite, pagina)
    return logs


@router.get("/rango-fechas/")
async def obtener_logs_por_fechas(
    fecha_inicio: str,
    fecha_fin: str,
    limite: int = Query(100, le=1000),
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Obtener logs dentro de un rango de fechas (formato: YYYY-MM-DD HH:MM:SS)"""
    try:
        f_inicio = datetime.fromisoformat(fecha_inicio)
        f_fin = datetime.fromisoformat(fecha_fin)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    logs = await repo.obtener_por_rango_fechas(f_inicio, f_fin, limite)
    return logs


@router.delete("/{log_id}")
async def eliminar_log(
    log_id: str,
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Eliminar un log por su ID"""
    eliminado = await repo.eliminar_por_id(log_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Log no encontrado")
    return {"mensaje": "Log eliminado exitosamente"}


@router.post("/limpiar/{dias}")
async def limpiar_logs_antiguos(
    dias: int = 30,
    repo: LogActividadRepository = Depends(get_log_repository)
):
    """Eliminar logs más antiguos que N días"""
    cantidad = await repo.limpiar_logs_antiguos(dias)
    return {"mensaje": f"Se eliminaron {cantidad} logs"}
