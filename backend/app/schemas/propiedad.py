from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PropiedadBase(BaseModel):
    propietario_id: int
    nombre: str
    descripcion: str | None = None
    tipo: str
    ciudad: str
    direccion: str
    ubicacion: str | None = None
    precio: float
    amenidades: dict | None = None
    tags: list[str] | None = None


class PropiedadCreate(PropiedadBase):
    pass


class PropiedadResponse(PropiedadBase):
    id: int
    estado: str
    rating: float | None = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
