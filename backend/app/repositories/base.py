from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import inspect

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Clase base para todos los repositories PostgreSQL.
    Implementa SOLID (DRY - No repetir código) y elimina boilerplate.
    
    Uso:
        class UsuarioRepository(BaseRepository[Usuario]):
            def __init__(self, db: Session):
                super().__init__(db, Usuario)
    """

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def obtener_por_id(self, id: int) -> Optional[T]:
        """Obtener una entidad por su ID"""
        return self.db.query(self.model).filter(
            self.model.id == id
        ).first()

    def listar_todos(self) -> List[T]:
        """Obtener todas las entidades"""
        return self.db.query(self.model).all()

    def crear(self, **kwargs) -> T:
        """
        Prepara una nueva entidad para ser persistida.
        IMPORTANTE: NO hace commit. El commit lo controla el router
        para poder componer múltiples operaciones en una sola transacción.
        """
        entidad = self.model(**kwargs)
        self.db.add(entidad)
        return entidad

    def actualizar(self, id: int, datos: dict) -> Optional[T]:
        """
        Aplica cambios a una entidad existente en memoria.
        IMPORTANTE: NO hace commit. El commit lo controla el router.
        """
        entidad = self.obtener_por_id(id)
        if not entidad:
            return None

        for clave, valor in datos.items():
            # Solo actualizar atributos que existan en el modelo y no sean la PK
            if hasattr(entidad, clave) and clave != "id":
                setattr(entidad, clave, valor)

        return entidad

    def eliminar(self, id: int) -> Optional[T]:
        """
        Marca una entidad para ser eliminada.
        IMPORTANTE: NO hace commit. El commit lo controla el router.
        Devuelve la entidad eliminada (o None si no existe) para poder
        usarla en logs de auditoría antes de que desaparezca.
        """
        entidad = self.obtener_por_id(id)
        if not entidad:
            return None

        self.db.delete(entidad)
        return entidad

    def contar(self) -> int:
        """Contar total de entidades"""
        return self.db.query(self.model).count()

    def existe(self, id: int) -> bool:
        """Verificar si existe una entidad por su ID"""
        return self.obtener_por_id(id) is not None

    def obtener_columnas(self) -> list[str]:
        """Obtener nombres de columnas del modelo (útil para debugging)"""
        mapper = inspect(self.model)
        return [col.name for col in mapper.columns]
