from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import EstadoPropiedad

class PropiedadBase(BaseModel):
    propietario_id: int
    nombre: str
    descripcion: str | None = None
    tipo: str
    ciudad: str
    direccion: str
    ubicacion: str | None = None
    precio: float = Field(..., gt=0)
    amenidades: dict | None = None
    tags: list[str] | None = None

    @field_validator('tipo')
    @classmethod
    def normalizar_tipo(cls, v: str) -> str:
        TIPOS_VALIDOS = {'departamento', 'casa', 'cabaña', 'habitacion'}
        if v is not None:
            v = v.lower().strip()
            if v not in TIPOS_VALIDOS:
                raise ValueError(f"Tipo inválido '{v}'. Valores permitidos: {sorted(TIPOS_VALIDOS)}")
        return v


class PropiedadCreate(PropiedadBase):
    pass

class PropiedadResponse(PropiedadBase):
    id: int
    estado: EstadoPropiedad
    rating: float | None = None
    creado_en: datetime
    model_config = ConfigDict(from_attributes=True)