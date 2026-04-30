from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"), nullable=False)
    huesped_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_checkin: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_checkout: Mapped[date] = mapped_column(Date, nullable=False)
    precio_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    propiedad = relationship("Propiedad", back_populates="reservas")
    huesped = relationship("Usuario", back_populates="reservas")
    resena = relationship("Resena", back_populates="reserva", uselist=False)
