from enum import Enum


class EstadoPropiedad(str, Enum):
    DISPONIBLE = "disponible"
    OCUPADA = "ocupada"
    MANTENIMIENTO = "mantenimiento"
    ELIMINADA = "eliminada"


class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"
