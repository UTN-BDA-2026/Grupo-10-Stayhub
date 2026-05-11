import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def get_password_hash(password: str) -> str:
    # Hasheo de contraseña seguro usando SHA-256 (Built-in de Python)
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()


@router.get("/{id}", response_model=UsuarioResponse)
def obtener_usuario(id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("/", response_model=UsuarioResponse, status_code=201)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Separar la información
    datos_usuario = payload.model_dump()
    
    # 2. Tomar el password en texto plano y eliminarlo del diccionario
    password_plano = datos_usuario.pop("password")
    
    # 3. Incorporar el hash en su lugar por seguridad
    datos_usuario["password_hash"] = get_password_hash(password_plano)
    
    usuario = Usuario(**datos_usuario)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
