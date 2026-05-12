from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    propiedades = relationship("Propiedad", back_populates="propietario")
    reservas = relationship("Reserva", back_populates="huesped")
    resenas = relationship("Resena", back_populates="huesped")
    logs_actividad = relationship("LogActividad", back_populates="usuario")
