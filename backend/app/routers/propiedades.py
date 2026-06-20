from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db, get_mongo_db
from app.repositories.propiedad import PropiedadRepository
from app.utils.log_utils import registrar_actividad
from app.schemas.propiedad import PropiedadCreate, PropiedadResponse

router = APIRouter(prefix="/propiedades", tags=["Propiedades"])


def get_propiedad_repository(db: Session = Depends(get_db)) -> PropiedadRepository:
    return PropiedadRepository(db)


@router.get("/", response_model=list[PropiedadResponse])
def listar_propiedades(
    ciudad: str | None = Query(None),
    tipo: str | None = Query(None),
    precio_min: float | None = Query(None),
    precio_max: float | None = Query(None),
    repo: PropiedadRepository = Depends(get_propiedad_repository),
):
    return repo.listar_todos(ciudad, tipo, precio_min, precio_max)


@router.get("/{id}", response_model=PropiedadResponse)
def obtener_propiedad(id: int, repo: PropiedadRepository = Depends(get_propiedad_repository)):
    propiedad = repo.obtener_por_id(id)
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return propiedad


@router.post("/", response_model=PropiedadResponse, status_code=201)
def crear_propiedad(
    payload: PropiedadCreate,
    db: Session = Depends(get_db),
    repo: PropiedadRepository = Depends(get_propiedad_repository),
):
    try:
        propiedad = repo.crear(payload)
        db.commit()
        db.refresh(propiedad)
        return propiedad

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad: verifique propietario_id.")

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al crear la propiedad.")


@router.put("/{id}", response_model=PropiedadResponse)
def actualizar_propiedad(
    id: int,
    payload: PropiedadCreate,
    db: Session = Depends(get_db),
    repo: PropiedadRepository = Depends(get_propiedad_repository),
):
    try:
        propiedad = repo.actualizar(id, payload.model_dump())
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        db.commit()
        db.refresh(propiedad)
        return propiedad

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al actualizar la propiedad.")


@router.delete("/{id}", response_model=PropiedadResponse)
def eliminar_propiedad(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    repo: PropiedadRepository = Depends(get_propiedad_repository),
):
    try:
        propiedad = repo.eliminar(id)
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        db.commit()

        background_tasks.add_task(
            registrar_actividad,
            db=get_mongo_db(),
            usuario_id=propiedad.propietario_id,
            accion="DELETE",
            tabla="propiedades",
            registro_id=propiedad.id,
            detalle={"nombre": propiedad.nombre}
        )

        return propiedad

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al eliminar la propiedad.")
