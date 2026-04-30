from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReservaBase(BaseModel):
    propiedad_id: int
    huesped_id: int
    fecha_checkin: date
    fecha_checkout: date
    precio_total: float


class ReservaCreate(ReservaBase):
    estado: str = "pendiente"


class ReservaEstadoUpdate(BaseModel):
    estado: str


class ReservaResponse(ReservaBase):
    id: int
    estado: str
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
