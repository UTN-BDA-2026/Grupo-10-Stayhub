from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.propiedad import Propiedad
from app.models.reserva import Reserva
from app.models.enums import EstadoReserva
from app.schemas.reserva import ReservaCreate, ReservaEstadoUpdate
from app.repositories.base import BaseRepository


class ReservaRepository(BaseRepository[Reserva]):
    """Repository para Reserva. Hereda CRUD base de BaseRepository."""

    def __init__(self, db: Session):
        super().__init__(db, Reserva)

    def listar_todos(
        self,
        estado: Optional[str] = None,
        huesped_id: Optional[int] = None,
        propiedad_id: Optional[int] = None,
    ) -> list[Reserva]:
        """Obtener reservas con filtros opcionales"""
        query = self.db.query(Reserva)

        if estado is not None:
            query = query.filter(Reserva.estado == estado)
        if huesped_id is not None:
            query = query.filter(Reserva.huesped_id == huesped_id)
        if propiedad_id is not None:
            query = query.filter(Reserva.propiedad_id == propiedad_id)

        return query.all()

    def validar_disponibilidad(
        self,
        propiedad_id: int,
        fecha_checkin: datetime,
        fecha_checkout: datetime,
    ) -> bool:
        """Validar si la propiedad está disponible en las fechas solicitadas"""
        # Verificar que la propiedad existe
        propiedad = self.db.query(Propiedad).filter(
            Propiedad.id == propiedad_id
        ).with_for_update().first()
        
        if not propiedad:
            return False

        # Verificar superposición de fechas
        superposicion = self.db.query(Reserva).filter(
            Reserva.propiedad_id == propiedad_id,
            Reserva.estado.in_([EstadoReserva.CONFIRMADA, EstadoReserva.PENDIENTE]),
            Reserva.fecha_checkin < fecha_checkout,
            Reserva.fecha_checkout > fecha_checkin,
        ).first()

        return superposicion is None

    def crear(self, payload: ReservaCreate) -> Reserva:
        """Crear una nueva reserva con validación"""
        # Validar disponibilidad
        if not self.validar_disponibilidad(
            payload.propiedad_id,
            payload.fecha_checkin,
            payload.fecha_checkout,
        ):
            raise ValueError(
                "La propiedad ya se encuentra reservada en las fechas solicitadas."
            )

        # Crear reserva
        datos_reserva = payload.model_dump()
        datos_reserva["creado_en"] = datetime.now(timezone.utc)

        reserva = Reserva(**datos_reserva)
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def actualizar_estado(self, reserva_id: int, payload: ReservaEstadoUpdate) -> Optional[Reserva]:
        """Actualizar el estado de una reserva"""
        reserva = self.obtener_por_id(reserva_id)
        if not reserva:
            return None

        reserva.estado = payload.estado
        self.db.commit()
        self.db.refresh(reserva)
        return reserva
