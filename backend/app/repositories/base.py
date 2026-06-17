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
        """Crear una nueva entidad"""
        entidad = self.model(**kwargs)
        self.db.add(entidad)
        self.db.commit()
        self.db.refresh(entidad)
        return entidad

    def actualizar(self, id: int, datos: dict) -> Optional[T]:
        """Actualizar una entidad existente"""
        entidad = self.obtener_por_id(id)
        if not entidad:
            return None

        for clave, valor in datos.items():
            # Solo actualizar atributos que existan en el modelo y no sean la PK
            if hasattr(entidad, clave) and clave != "id":
                setattr(entidad, clave, valor)

        self.db.commit()
        self.db.refresh(entidad)
        return entidad

    def eliminar(self, id: int) -> bool:
        """Eliminar una entidad por su ID"""
        entidad = self.obtener_por_id(id)
        if not entidad:
            return False

        self.db.delete(entidad)
        self.db.commit()
        return True

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
