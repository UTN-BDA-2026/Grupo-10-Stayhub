from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from app.models.enums import EstadoReserva


class ReservaBase(BaseModel):
    propiedad_id: int
    huesped_id: int
    fecha_checkin: date
    fecha_checkout: date
    precio_total: float


class ReservaCreate(ReservaBase):
    estado: EstadoReserva = EstadoReserva.PENDIENTE


class ReservaEstadoUpdate(BaseModel):
    estado: EstadoReserva


class ReservaResponse(ReservaBase):
    id: int
    estado: EstadoReserva
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
