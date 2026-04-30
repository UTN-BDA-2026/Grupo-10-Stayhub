from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.propiedad import Propiedad
from app.schemas.propiedad import PropiedadCreate, PropiedadResponse

router = APIRouter(prefix="/propiedades", tags=["Propiedades"])


@router.get("/", response_model=list[PropiedadResponse])
def listar_propiedades(
    ciudad: str | None = Query(None),
    tipo: str | None = Query(None),
    precio_min: float | None = Query(None),
    precio_max: float | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Propiedad)

    if ciudad is not None:
        query = query.filter(Propiedad.ciudad == ciudad)
    if tipo is not None:
        query = query.filter(Propiedad.tipo == tipo)
    if precio_min is not None:
        query = query.filter(Propiedad.precio >= precio_min)
    if precio_max is not None:
        query = query.filter(Propiedad.precio <= precio_max)

    return query.all()


@router.get("/{id}", response_model=PropiedadResponse)
def obtener_propiedad(id: int, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == id).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return propiedad


@router.post("/", response_model=PropiedadResponse, status_code=201)
def crear_propiedad(payload: PropiedadCreate, db: Session = Depends(get_db)):
    propiedad = Propiedad(**payload.model_dump())
    db.add(propiedad)
    db.commit()
    db.refresh(propiedad)
    return propiedad


@router.put("/{id}", response_model=PropiedadResponse)
def actualizar_propiedad(id: int, payload: PropiedadCreate, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == id).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    for campo, valor in payload.model_dump().items():
        setattr(propiedad, campo, valor)

    db.commit()
    db.refresh(propiedad)
    return propiedad


@router.delete("/{id}", response_model=PropiedadResponse)
def eliminar_propiedad(id: int, db: Session = Depends(get_db)):
    propiedad = db.query(Propiedad).filter(Propiedad.id == id).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    propiedad.estado = "eliminada"
    db.commit()
    db.refresh(propiedad)
    return propiedad
