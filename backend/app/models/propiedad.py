from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Propiedad(Base):
    __tablename__ = "propiedades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    propietario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    ubicacion: Mapped[str] = mapped_column(String, nullable=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amenidades: Mapped[dict] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="disponible")
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    propietario = relationship("Usuario", back_populates="propiedades")
    reservas = relationship("Reserva", back_populates="propiedad")
    resenas = relationship("Resena", back_populates="propiedad")

    __table_args__ = (
        Index('ix_ciudad_estado', "ciudad", "estado"),
        Index('ix_amenidades_gin', "amenidades", postgresql_using='gin'),
    )
