from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, get_mongo_db
from app.repositories.reserva import ReservaRepository
from app.utils.log_utils import registrar_actividad
from app.schemas.reserva import ReservaCreate, ReservaEstadoUpdate, ReservaResponse

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def get_reserva_repository(db: Session = Depends(get_db)) -> ReservaRepository:
    return ReservaRepository(db)


@router.get("/", response_model=list[ReservaResponse])
def listar_reservas(
    estado: str | None = None,
    huesped_id: int | None = None,
    propiedad_id: int | None = None,
    repo: ReservaRepository = Depends(get_reserva_repository),
):
    return repo.listar_todos(estado, huesped_id, propiedad_id)


@router.get("/{id}", response_model=ReservaResponse)
def obtener_reserva(id: int, repo: ReservaRepository = Depends(get_reserva_repository)):
    reserva = repo.obtener_por_id(id)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


@router.post("/", response_model=ReservaResponse, status_code=201)
def crear_reserva(
    payload: ReservaCreate, 
    background_tasks: BackgroundTasks,
    repo: ReservaRepository = Depends(get_reserva_repository)
):
    try:
        reserva = repo.crear(payload)
        
        background_tasks.add_task(
            registrar_actividad,
            db=get_mongo_db(),
            usuario_id=reserva.huesped_id,
            accion="CREATE",
            tabla="reservas",
            registro_id=reserva.id,
            detalle={"propiedad_id": reserva.propiedad_id, "estado": reserva.estado}
        )
        
        return reserva
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al procesar la reserva.")


@router.patch("/{id}/estado", response_model=ReservaResponse)
def actualizar_estado_reserva(id: int, payload: ReservaEstadoUpdate, repo: ReservaRepository = Depends(get_reserva_repository)):
    reserva = repo.actualizar_estado(id, payload)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva
