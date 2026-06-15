from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.resena import ResenaRepository
from app.schemas.resena import ResenaCreate, ResenaResponse

router = APIRouter(prefix="/reseñas", tags=["reseñas"])


def get_resena_repository(db: Session = Depends(get_db)) -> ResenaRepository:
    return ResenaRepository(db)


@router.get("/", response_model=list[ResenaResponse])
async def listar_reseñas(
    limite: int = 100,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Listar todas las reseñas"""
    return repo.listar_todas(limite=limite)


@router.get("/{resena_id}", response_model=ResenaResponse)
async def obtener_reseña(
    resena_id: int,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Obtener una reseña por ID"""
    resena = repo.obtener_por_id(resena_id)
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return resena


@router.get("/propiedad/{propiedad_id}", response_model=list[ResenaResponse])
async def obtener_reseñas_propiedad(
    propiedad_id: int,
    limite: int = 50,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Obtener reseñas de una propiedad"""
    return repo.obtener_por_propiedad(propiedad_id, limite=limite)


@router.get("/huesped/{huesped_id}", response_model=list[ResenaResponse])
async def obtener_reseñas_huesped(
    huesped_id: int,
    limite: int = 50,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Obtener reseñas escritas por un huésped"""
    return repo.obtener_por_huesped(huesped_id, limite=limite)


@router.post("/", response_model=ResenaResponse)
async def crear_reseña(
    payload: ResenaCreate,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Crear una nueva reseña"""
    return repo.crear(payload)


@router.put("/{resena_id}", response_model=ResenaResponse)
async def actualizar_reseña(
    resena_id: int,
    payload: dict,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Actualizar una reseña"""
    resena = repo.actualizar(resena_id, payload)
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return resena


@router.delete("/{resena_id}")
async def eliminar_reseña(
    resena_id: int,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Eliminar una reseña"""
    if not repo.eliminar(resena_id):
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return {"mensaje": "Reseña eliminada exitosamente"}


@router.get("/propiedad/{propiedad_id}/promedio")
async def obtener_promedio_propiedad(
    propiedad_id: int,
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Obtener puntuación promedio de una propiedad"""
    promedio = repo.obtener_promedio_propiedad(propiedad_id)
    if promedio is None:
        return {"promedio": 0, "cantidad": 0}
    
    cantidad = len(repo.obtener_por_propiedad(propiedad_id))
    return {"promedio": promedio, "cantidad": cantidad}
