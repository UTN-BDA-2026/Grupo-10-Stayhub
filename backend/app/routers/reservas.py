from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reserva import Reserva
from app.schemas.reserva import ReservaCreate, ReservaEstadoUpdate, ReservaResponse

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.get("/", response_model=list[ReservaResponse])
def listar_reservas(
    estado: str | None = None,
    huesped_id: int | None = None,
    propiedad_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Reserva)

    if estado is not None:
        query = query.filter(Reserva.estado == estado)
    if huesped_id is not None:
        query = query.filter(Reserva.huesped_id == huesped_id)
    if propiedad_id is not None:
        query = query.filter(Reserva.propiedad_id == propiedad_id)

    return query.all()


@router.get("/{id}", response_model=ReservaResponse)
def obtener_reserva(id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).filter(Reserva.id == id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


@router.post("/", response_model=ReservaResponse, status_code=201)
def crear_reserva(payload: ReservaCreate, db: Session = Depends(get_db)):
    reserva = Reserva(**payload.model_dump())
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


@router.patch("/{id}/estado", response_model=ReservaResponse)
def actualizar_estado_reserva(id: int, payload: ReservaEstadoUpdate, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).filter(Reserva.id == id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    reserva.estado = payload.estado
    db.commit()
    db.refresh(reserva)
    return reserva
