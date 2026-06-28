from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ResenaBase(BaseModel):
    puntuacion: int = Field(..., ge=1, le=5, description="Puntuación de 1 a 5")
    comentario: str | None = None


class ResenaCreate(ResenaBase):
    reserva_id: int
    # propiedad_id y huesped_id se derivan de la reserva en el repository.
    # No se aceptan del cliente para evitar inconsistencias semánticas.


class ResenaResponse(ResenaBase):
    id: int
    reserva_id: int
    propiedad_id: int
    huesped_id: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)