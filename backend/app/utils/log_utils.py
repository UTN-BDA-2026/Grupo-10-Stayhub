"""
Utilidad para registrar actividades de usuarios en MongoDB
"""
from datetime import datetime
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.log_actividad import LogActividadRepository
from app.schemas.log_actividad import LogActividadCreate


async def registrar_actividad(
    db: AsyncIOMotorDatabase,
    usuario_id: Optional[int],
    accion: str,
    tabla: Optional[str] = None,
    registro_id: Optional[int] = None,
    detalle: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
):
    """
    Registra una actividad del usuario en MongoDB.
    
    Args:
        db: Base de datos de MongoDB
        usuario_id: ID del usuario (puede ser None para acciones no autenticadas)
        accion: Tipo de acción (ej: CREATE, UPDATE, DELETE, READ)
        tabla: Nombre de la tabla afectada
        registro_id: ID del registro afectado
        detalle: Información adicional en formato dict
        ip: Dirección IP del cliente
    
    Ejemplo:
        await registrar_actividad(
            db=db,
            usuario_id=1,
            accion="CREATE",
            tabla="propiedades",
            registro_id=100,
            detalle={"nombre": "Casa playa", "precio": 150000},
            ip="192.168.1.1"
        )
    """
    try:
        repo = LogActividadRepository(db)
        
        log_data = LogActividadCreate(
            usuario_id=usuario_id,
            accion=accion,
            tabla=tabla,
            registro_id=registro_id,
            detalle=detalle,
            ip=ip,
            creado_en=datetime.utcnow()
        )
        
        log_id = await repo.crear(log_data)
        print(f"✓ Log registrado: {log_id}")
        return log_id
    except Exception as e:
        print(f"✗ Error al registrar actividad: {str(e)}")
        # No lanzamos la excepción para no interrumpir la operación principal
        return None
