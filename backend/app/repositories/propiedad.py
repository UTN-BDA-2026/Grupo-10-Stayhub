from typing import Optional
from sqlalchemy import and_, or_

from app.models.propiedad import Propiedad
from app.repositories.base import BaseRepository

class PropiedadRepository(BaseRepository[Propiedad]):
    
    def buscar_propiedades(
        self,
        ciudad: Optional[str] = None,
        tipo: Optional[str] = None,
        precio_min: Optional[float] = None,
        precio_max: Optional[float] = None,
        amenidades: Optional[list[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """
        Búsqueda avanzada con múltiples filtros
        
        Amenidades: ["wifi", "piscina", "aire_acondicionado"]
        """
        query = self.db.query(Propiedad).filter(
            Propiedad.estado == "disponible"
        )
        
        # Filtros individuales
        if ciudad:
            query = query.filter(Propiedad.ciudad.ilike(f"%{ciudad}%"))
        
        if tipo:
            query = query.filter(Propiedad.tipo == tipo)
        
        if precio_min is not None:
            query = query.filter(Propiedad.precio >= precio_min)
        
        if precio_max is not None:
            query = query.filter(Propiedad.precio <= precio_max)
        
        # Filtro de amenidades (JSON)
        if amenidades:
            for amenidad in amenidades:
                query = query.filter(
                    Propiedad.amenidades[amenidad].astext == "true"
                )
        
        # Contar ANTES de paginar
        total = query.count()
        
        # Paginar
        propiedades = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": propiedades
        }