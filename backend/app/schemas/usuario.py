from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsuarioBase(BaseModel):
    nombre: str
    email: str
    rol: str


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioResponse(UsuarioBase):
    id: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
