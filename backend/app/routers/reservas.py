
@router.post("/", response_model=ReservaResponse, status_code=201)
def crear_reserva(
    payload: ReservaCreate,
    db: Session = Depends(get_db),
    repo: ReservaRepository = Depends(get_reserva_repo),
    usuario_id: int = Depends(get_usuario_id)  # Del JWT
):
    """
    Crear una reserva de forma segura
    
    Garantía: No hay race conditions de disponibilidad
    """
    try:
        # TODAS las operaciones en una sola transacción
        reserva = repo.crear_reserva_segura(
            propiedad_id=payload.propiedad_id,
            huesped_id=usuario_id,
            fecha_checkin=payload.fecha_checkin,
            fecha_checkout=payload.fecha_checkout,
            precio_total=payload.precio_total
        )
        
        # Solo si llegamos aquí, se confirma
        db.commit()
        db.refresh(reserva)
        
        return reserva
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creando reserva")