from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.propiedad import Propiedad
from app.models.reserva import Reserva
from app.models.enums import EstadoReserva
from app.schemas.reserva import ReservaCreate, ReservaEstadoUpdate
from app.repositories.base import BaseRepository

class ReservaRepository(BaseRepository[Reserva]):
    
    def crear_reserva_segura(
        self,
        propiedad_id: int,
        huesped_id: int,
        fecha_checkin: date,
        fecha_checkout: date,
        precio_total: Decimal
    ) -> Reserva:
        """
        Crear reserva CON garantía de que la propiedad está disponible
        
        Usa SELECT FOR UPDATE para evitar race conditions
        """
        # PASO 1: Lock de la propiedad para que nadie más la toque
        propiedad = self.db.query(Propiedad).with_for_update().filter(
            Propiedad.id == propiedad_id
        ).first()
        
        if not propiedad:
            raise ValueError("Propiedad no existe")
        
        if propiedad.estado != "disponible":
            raise ValueError("Propiedad no está disponible")
        
        # PASO 2: Verificar conflictos de fechas
        # (Nadie puede interferir porque la propiedad está locked)
        conflicto = self.db.query(Reserva).filter(
            Reserva.propiedad_id == propiedad_id,
            Reserva.estado.in_(["confirmada", "pendiente"]),
            # Hay conflicto si: nueva_fecha_inicio < reserva_existente_fin
            #             AND: nueva_fecha_fin > reserva_existente_inicio
            Reserva.fecha_checkin < fecha_checkout,
            Reserva.fecha_checkout > fecha_checkin
        ).first()
        
        if conflicto:
            raise ValueError(
                f"Propiedad ocupada {conflicto.fecha_checkin} a {conflicto.fecha_checkout}"
            )
        
        # PASO 3: Crear la reserva (dentro de la misma transacción)
        nueva_reserva = Reserva(
            propiedad_id=propiedad_id,
            huesped_id=huesped_id,
            fecha_checkin=fecha_checkin,
            fecha_checkout=fecha_checkout,
            precio_total=precio_total,
            estado="pendiente"
        )
        self.db.add(nueva_reserva)
        
        # El lock se libera cuando la transacción commitea
        return nueva_reserva