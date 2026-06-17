from typing import Optional

from sqlalchemy.orm import Session

from app.models.propiedad import Propiedad
from app.models.enums import EstadoPropiedad
from app.schemas.propiedad import PropiedadCreate
from app.repositories.base import BaseRepository


class PropiedadRepository(BaseRepository[Propiedad]):
    """Repository para Propiedad. Hereda CRUD base de BaseRepository."""

    def __init__(self, db: Session):
        super().__init__(db, Propiedad)

    def listar_todos(
        self,
        ciudad: Optional[str] = None,
        tipo: Optional[str] = None,
        precio_min: Optional[float] = None,
        precio_max: Optional[float] = None,
    ) -> list[Propiedad]:
        """Obtener propiedades con filtros opcionales"""
        query = self.db.query(Propiedad)

        if ciudad is not None:
            query = query.filter(Propiedad.ciudad == ciudad)
        if tipo is not None:
            query = query.filter(Propiedad.tipo == tipo)
        if precio_min is not None:
            query = query.filter(Propiedad.precio >= precio_min)
        if precio_max is not None:
            query = query.filter(Propiedad.precio <= precio_max)

        return query.all()

    def crear(self, payload: PropiedadCreate) -> Propiedad:
        """Crear una nueva propiedad"""
        return super().crear(**payload.model_dump())

    def actualizar(self, propiedad_id: int, payload: PropiedadCreate) -> Optional[Propiedad]:
        """Actualizar una propiedad"""
        return super().actualizar(propiedad_id, payload.model_dump())

    def eliminar(self, propiedad_id: int) -> Optional[Propiedad]:
        """Marcar una propiedad como eliminada (soft delete)"""
        propiedad = self.obtener_por_id(propiedad_id)
        if not propiedad:
            return None

        propiedad.estado = EstadoPropiedad.ELIMINADA
        self.db.commit()
        self.db.refresh(propiedad)
        return propiedad
