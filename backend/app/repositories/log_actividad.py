from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.log_actividad import LogActividadCreate


class LogActividadRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["logs_actividad"]

    async def crear(self, log_data: LogActividadCreate) -> str:
        """Crear un nuevo log de actividad"""
        document = log_data.model_dump(exclude_none=True)
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def obtener_por_id(self, log_id: str):
        """Obtener un log por su ID"""
        try:
            obj_id = ObjectId(log_id)
            return await self.collection.find_one({"_id": obj_id})
        except Exception:
            return None

    async def obtener_por_usuario(self, usuario_id: int, limite: int = 100):
        """Obtener logs de un usuario específico"""
        logs = []
        async for log in self.collection.find({"usuario_id": usuario_id}).limit(limite).sort("creado_en", -1):
            log["id"] = str(log["_id"])
            logs.append(log)
        return logs

    async def obtener_por_tabla(self, tabla: str, limite: int = 100):
        """Obtener logs de una tabla específica"""
        logs = []
        async for log in self.collection.find({"tabla": tabla}).limit(limite).sort("creado_en", -1):
            log["id"] = str(log["_id"])
            logs.append(log)
        return logs

    async def obtener_todos(self, limite: int = 100, pagina: int = 1):
        """Obtener todos los logs con paginación"""
        skip = (pagina - 1) * limite
        logs = []
        async for log in self.collection.find().skip(skip).limit(limite).sort("creado_en", -1):
            log["id"] = str(log["_id"])
            logs.append(log)
        return logs

    async def obtener_por_rango_fechas(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        limite: int = 100
    ):
        """Obtener logs dentro de un rango de fechas"""
        logs = []
        query = {
            "creado_en": {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            }
        }
        async for log in self.collection.find(query).limit(limite).sort("creado_en", -1):
            log["id"] = str(log["_id"])
            logs.append(log)
        return logs

    async def contar_por_usuario(self, usuario_id: int) -> int:
        """Contar logs de un usuario"""
        return await self.collection.count_documents({"usuario_id": usuario_id})

    async def contar_por_accion(self, accion: str) -> int:
        """Contar logs por tipo de acción"""
        return await self.collection.count_documents({"accion": accion})

    async def eliminar_por_id(self, log_id: str) -> bool:
        """Eliminar un log por su ID"""
        try:
            obj_id = ObjectId(log_id)
            result = await self.collection.delete_one({"_id": obj_id})
            return result.deleted_count > 0
        except Exception:
            return False

    async def limpiar_logs_antiguos(self, dias: int = 30):
        """Eliminar logs más antiguos que N días"""
        fecha_limite = datetime.utcnow()
        from datetime import timedelta
        fecha_limite = fecha_limite - timedelta(days=dias)
        
        result = await self.collection.delete_many({"creado_en": {"$lt": fecha_limite}})
        return result.deleted_count
