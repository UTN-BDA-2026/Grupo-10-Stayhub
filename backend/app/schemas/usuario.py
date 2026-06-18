from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol: Literal["huesped", "propietario", "admin"]


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)


class UsuarioResponse(UsuarioBase):
    id: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    mensaje: str
