from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from datetime import datetime, timezone
from sqlalchemy import or_, and_
from app.models.reserva import Reserva
from app.models.propiedad import Propiedad
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
    try:
        propiedad = db.query(Propiedad).filter(Propiedad.id == payload.propiedad_id).with_for_update().first()
        
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
            
        superposicion = db.query(Reserva).filter(
            Reserva.propiedad_id == payload.propiedad_id,
            Reserva.estado.in_(["confirmada", "pendiente"]),
            Reserva.fecha_checkin < payload.fecha_checkout,
            Reserva.fecha_checkout > payload.fecha_checkin
        ).first()
        
        if superposicion:
            raise HTTPException(
                status_code=400, 
                detail="La propiedad ya se encuentra reservada en las fechas solicitadas."
            )
            
        datos_reserva = payload.model_dump()
        datos_reserva["creado_en"] = datetime.now(timezone.utc)
        
        reserva = Reserva(**datos_reserva)
        db.add(reserva)
        db.commit() 
        db.refresh(reserva)
        return reserva
        
    except HTTPException:
        db.rollback() 
        raise
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail="Error interno al procesar la reserva.")


@router.patch("/{id}/estado", response_model=ReservaResponse)
def actualizar_estado_reserva(id: int, payload: ReservaEstadoUpdate, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).filter(Reserva.id == id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    reserva.estado = payload.estado
    db.commit()
    db.refresh(reserva)
    return reserva
