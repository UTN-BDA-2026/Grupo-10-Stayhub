import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hashear contraseña usando SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def listar_todos(self) -> list[Usuario]:
        """Obtener todos los usuarios"""
        return self.db.query(Usuario).all()

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtener un usuario por su ID"""
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtener un usuario por su email"""
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def crear(self, payload: UsuarioCreate) -> Usuario:
        """Crear un nuevo usuario"""
        datos_usuario = payload.model_dump()
        
        # Extraer contraseña en texto plano
        password_plano = datos_usuario.pop("password")
        
        # Hashear y guardar
        datos_usuario["password_hash"] = self.get_password_hash(password_plano)
        
        usuario = Usuario(**datos_usuario)
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def actualizar(self, usuario_id: int, datos: dict) -> Optional[Usuario]:
        """Actualizar un usuario"""
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return None
        
        for campo, valor in datos.items():
            if hasattr(usuario, campo) and campo != "id":
                setattr(usuario, campo, valor)
        
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def eliminar(self, usuario_id: int) -> bool:
        """Eliminar un usuario"""
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        
        self.db.delete(usuario)
        self.db.commit()
        return True
