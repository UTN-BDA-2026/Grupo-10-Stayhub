from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def get_usuario_repository(db: Session = Depends(get_db)) -> UsuarioRepository:
    return UsuarioRepository(db)


@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(repo: UsuarioRepository = Depends(get_usuario_repository)):
    return repo.listar_todos()


@router.get("/{id}", response_model=UsuarioResponse)
def obtener_usuario(id: int, repo: UsuarioRepository = Depends(get_usuario_repository)):
    usuario = repo.obtener_por_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("/", response_model=UsuarioResponse, status_code=201)
def crear_usuario(payload: UsuarioCreate, repo: UsuarioRepository = Depends(get_usuario_repository)):
    usuario = repo.crear(payload)
    return usuario
