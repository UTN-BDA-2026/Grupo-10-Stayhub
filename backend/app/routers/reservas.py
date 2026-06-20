from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
    db: Session = Depends(get_db),
    repo: ReservaRepository = Depends(get_reserva_repository),
):
    """
    Crea una reserva con garantías ACID:
    - Atomicidad: el commit y el rollback están en el router.
    - Isolation: FOR UPDATE en validar_disponibilidad() bloquea la propiedad
      hasta que se confirme o descarte la transacción.
    - Consistency: CHECK constraints y FK garantizan datos válidos.
    - Durability: PostgreSQL escribe en WAL antes de confirmar.
    """
    try:
        # El repo valida disponibilidad (adquiere FOR UPDATE) y prepara la reserva
        reserva = repo.crear(payload)

        # El commit confirma TODO: el lock se libera, la reserva queda persistida
        db.commit()
        db.refresh(reserva)

        # Log de auditoría en segundo plano (no bloquea la respuesta)
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
        # Disponibilidad no válida — no hubo commit, el rollback limpia el lock
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError as e:
        # Violación de FK o CHECK constraint en la DB
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad: verifique propiedad_id y huesped_id.")

    except Exception:
        # Cualquier otro error inesperado — rollback siempre
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al procesar la reserva.")


@router.patch("/{id}/estado", response_model=ReservaResponse)
def actualizar_estado_reserva(
    id: int,
    payload: ReservaEstadoUpdate,
    db: Session = Depends(get_db),
    repo: ReservaRepository = Depends(get_reserva_repository),
):
    try:
        reserva = repo.actualizar_estado(id, payload)
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        db.commit()
        db.refresh(reserva)
        return reserva

    except HTTPException:
        raise  # Re-lanzar HTTPException sin envolverla

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar estado de la reserva.")
