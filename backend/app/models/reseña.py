from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import INET, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Resena(Base):
    __tablename__ = "reseñas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reserva_id: Mapped[int] = mapped_column(ForeignKey("reservas.id"), nullable=False)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"), nullable=False)
    huesped_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    puntuacion: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reserva = relationship("Reserva", back_populates="resena")
    propiedad = relationship("Propiedad", back_populates="resenas")
    huesped = relationship("Usuario", back_populates="resenas")


class LogActividad(Base):
    __tablename__ = "logs_actividad"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    tabla: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registro_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    usuario = relationship("Usuario", back_populates="logs_actividad")
