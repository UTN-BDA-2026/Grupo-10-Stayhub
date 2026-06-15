from typing import Optional

from sqlalchemy.orm import Session

from app.models.reseña import Resena
from app.schemas.resena import ResenaCreate


class ResenaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_todas(self, limite: int = 100) -> list[Resena]:
        """Obtener todas las reseñas"""
        return self.db.query(Resena).limit(limite).all()

    def obtener_por_id(self, resena_id: int) -> Optional[Resena]:
        """Obtener una reseña por su ID"""
        return self.db.query(Resena).filter(Resena.id == resena_id).first()

    def obtener_por_propiedad(self, propiedad_id: int, limite: int = 50) -> list[Resena]:
        """Obtener reseñas de una propiedad"""
        return self.db.query(Resena).filter(Resena.propiedad_id == propiedad_id).limit(limite).all()

    def obtener_por_huesped(self, huesped_id: int, limite: int = 50) -> list[Resena]:
        """Obtener reseñas escritas por un huésped"""
        return self.db.query(Resena).filter(Resena.huesped_id == huesped_id).limit(limite).all()

    def obtener_por_reserva(self, reserva_id: int) -> Optional[Resena]:
        """Obtener reseña de una reserva específica"""
        return self.db.query(Resena).filter(Resena.reserva_id == reserva_id).first()

    def crear(self, payload: ResenaCreate) -> Resena:
        """Crear una nueva reseña"""
        from datetime import datetime
        
        datos_resena = payload.model_dump()
        datos_resena["creado_en"] = datetime.utcnow()
        
        resena = Resena(**datos_resena)
        self.db.add(resena)
        self.db.commit()
        self.db.refresh(resena)
        return resena

    def actualizar(self, resena_id: int, datos: dict) -> Optional[Resena]:
        """Actualizar una reseña"""
        resena = self.obtener_por_id(resena_id)
        if not resena:
            return None
        
        for clave, valor in datos.items():
            if hasattr(resena, clave):
                setattr(resena, clave, valor)
        
        self.db.commit()
        self.db.refresh(resena)
        return resena

    def eliminar(self, resena_id: int) -> bool:
        """Eliminar una reseña"""
        resena = self.obtener_por_id(resena_id)
        if not resena:
            return False
        
        self.db.delete(resena)
        self.db.commit()
        return True

    def obtener_promedio_propiedad(self, propiedad_id: int) -> Optional[float]:
        """Obtener puntuación promedio de una propiedad"""
        from sqlalchemy import func
        
        resultado = self.db.query(func.avg(Resena.puntuacion)).filter(
            Resena.propiedad_id == propiedad_id
        ).scalar()
        
        return float(resultado) if resultado else None
