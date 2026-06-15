from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text
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
