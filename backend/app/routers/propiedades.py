from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db, get_mongo_db
from app.repositories.propiedad import PropiedadRepository
from app.utils.log_utils import registrar_actividad
from app.schemas.propiedad import PropiedadCreate, PropiedadResponse
from typing import Optional, List

@router.get("/", response_model=dict)
def buscar_propiedades(
    ciudad: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    precio_min: Optional[float] = Query(None),
    precio_max: Optional[float] = Query(None),
    amenidades: Optional[List[str]] = Query(None),
    skip: int = Query(0),
    limit: int = Query(20, le=100),
    repo: PropiedadRepository = Depends(get_propiedad_repo)
):
    """
    Buscar propiedades con filtros avanzados
    
    Ejemplos:
    - GET /propiedades?ciudad=Mendoza&tipo=casa
    - GET /propiedades?precio_min=100&precio_max=500
    - GET /propiedades?ciudad=Mendoza&amenidades=wifi&amenidades=piscina
    - GET /propiedades?ciudad=Mendoza&skip=0&limit=10
    """
    return repo.buscar_propiedades(
        ciudad=ciudad,
        tipo=tipo,
        precio_min=precio_min,
        precio_max=precio_max,
        amenidades=amenidades,
        skip=skip,
        limit=limit
    )