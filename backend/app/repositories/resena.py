from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.reseña import Resena
from app.models.reserva import Reserva
from app.models.enums import EstadoReserva
from app.schemas.resena import ResenaCreate
from app.repositories.base import BaseRepository


class ResenaRepository(BaseRepository[Resena]):
    """Repository para Reseña. Hereda CRUD base de BaseRepository."""

    def __init__(self, db: Session):
        super().__init__(db, Resena)

    def listar_todas(self, limite: int = 100) -> list[Resena]:
        """Obtener todas las reseñas"""
        return self.db.query(Resena).limit(limite).all()

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
        """
        Crear una nueva reseña derivando propiedad_id y huesped_id desde la reserva.

        Validaciones:
        - La reserva debe existir.
        - La reserva debe estar en estado 'completada'.
        - No puede existir ya una reseña para esa reserva (UNIQUE reserva_id).
        """
        # Cargar la reserva y validar su estado
        reserva = self.db.get(Reserva, payload.reserva_id)

        if not reserva:
            raise ValueError(f"La reserva {payload.reserva_id} no existe.")

        if reserva.estado != EstadoReserva.COMPLETADA:
            raise ValueError(
                f"Solo se pueden reseñar reservas completadas. "
                f"Estado actual: '{reserva.estado}'."
            )

        # Verificar que no exista ya una reseña para esta reserva
        if self.obtener_por_reserva(payload.reserva_id):
            raise ValueError(
                f"Ya existe una reseña para la reserva {payload.reserva_id}."
            )

        # Derivar IDs desde la reserva — ignorar cualquier valor que pudiera
        # venir del cliente para evitar inconsistencias semánticas
        resena = Resena(
            reserva_id=reserva.id,
            propiedad_id=reserva.propiedad_id,   # ← siempre desde la reserva
            huesped_id=reserva.huesped_id,        # ← siempre desde la reserva
            puntuacion=payload.puntuacion,
            comentario=payload.comentario,
            creado_en=datetime.now(timezone.utc),
        )
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