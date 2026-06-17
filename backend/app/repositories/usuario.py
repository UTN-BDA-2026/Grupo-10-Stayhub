from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate
from app.repositories.base import BaseRepository

# Configuramos bcrypt como el algoritmo de encriptación estándar
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsuarioRepository(BaseRepository[Usuario]):
    """Repository para Usuario. Hereda métodos base (CRUD) de BaseRepository."""

    def __init__(self, db: Session):
        super().__init__(db, Usuario)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hashear contraseña usando bcrypt (Seguro contra fuerza bruta)"""
        return pwd_context.hash(password)

    @staticmethod
    def verificar_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar si la contraseña plana coincide con el hash en la BD"""
        return pwd_context.verify(plain_password, hashed_password)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtener un usuario por su email"""
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def crear(self, payload: UsuarioCreate) -> Usuario:
        """Crear un nuevo usuario con contraseña hasheada"""
        datos_usuario = payload.model_dump()
        
        # Extraer contraseña en texto plano
        password_plano = datos_usuario.pop("password")
        
        # Hashear y guardar usando bcrypt
        datos_usuario["password_hash"] = self.get_password_hash(password_plano)
        
        return super().crear(**datos_usuario)