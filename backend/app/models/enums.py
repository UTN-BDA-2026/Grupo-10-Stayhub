from enum import Enum


class EstadoPropiedad(str, Enum):
    DISPONIBLE = "disponible"
    PAUSADA = "pausada"      # Alineado con CHECK constraint de la DB
    ELIMINADA = "eliminada"


class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"
