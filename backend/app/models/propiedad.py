from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSON, GIN
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Propiedad(Base):
    __tablename__ = "propiedades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    propietario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(String, nullable=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amenidades: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    propietario = relationship("Usuario", back_populates="propiedades")
    reservas = relationship("Reserva", back_populates="propiedad")
    resenas = relationship("Resena", back_populates="propiedad")

    # Índices Avanzados
    __table_args__ = (
        # 1. Índice Compuesto: Ideal para búsquedas combinadas. Ej: "Buscar propiedades en 'Mendoza' que estén 'Disponibles'"
        Index('ix_ciudad_estado', "ciudad", "estado"),
        # 2. Índice GIN: Ideal para buscar dentro de arreglos o JSON. Permite preguntar "Dónde hay Wifi dentro del JSON amenidades" rápidamente.
        Index('ix_amenidades_gin', "amenidades", postgresql_using='gin')
    )

