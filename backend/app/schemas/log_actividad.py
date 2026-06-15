from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LogActividadBase(BaseModel):
    usuario_id: Optional[int] = None
    accion: str = Field(..., min_length=1, max_length=100)
    tabla: Optional[str] = Field(None, max_length=100)
    registro_id: Optional[int] = None
    detalle: Optional[dict[str, Any]] = None
    ip: Optional[str] = None


class LogActividadCreate(LogActividadBase):
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class LogActividad(LogActividadBase):
    id: str = Field(..., alias="_id")
    creado_en: datetime

    class Config:
        populate_by_name = True
