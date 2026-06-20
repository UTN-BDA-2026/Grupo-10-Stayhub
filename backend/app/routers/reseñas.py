from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
    db: Session = Depends(get_db),
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Crear una nueva reseña"""
    try:
        resena = repo.crear(payload)
        db.commit()
        db.refresh(resena)
        return resena

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad: verifique reserva_id y huesped_id.")

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear la reseña.")


@router.put("/{resena_id}", response_model=ResenaResponse)
async def actualizar_reseña(
    resena_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Actualizar una reseña"""
    try:
        resena = repo.actualizar(resena_id, payload)
        if not resena:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")

        db.commit()
        db.refresh(resena)
        return resena

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al actualizar la reseña.")


@router.delete("/{resena_id}")
async def eliminar_reseña(
    resena_id: int,
    db: Session = Depends(get_db),
    repo: ResenaRepository = Depends(get_resena_repository)
):
    """Eliminar una reseña"""
    try:
        resena = repo.eliminar(resena_id)
        if not resena:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")

        db.commit()
        return {"mensaje": "Reseña eliminada exitosamente"}

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al eliminar la reseña.")


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
