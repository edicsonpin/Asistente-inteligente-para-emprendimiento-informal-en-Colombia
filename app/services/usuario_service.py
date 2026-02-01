from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

# ✅ CORREGIR: Cambiar de "usuario_repository" a "usuarios"
from repositories.usuarios import usuario_repository
from schemas.usuarios import UsuarioCreate, UsuarioUpdate, UsuarioInDB

class UsuarioService:
    def __init__(self):
        self.repository = usuario_repository

    def get_usuario(self, db: Session, usuario_id: int) -> Optional[UsuarioInDB]:
        usuario = self.repository.get(db, usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return usuario

    def get_usuarios(self, db: Session, skip: int = 0, limit: int = 100) -> List[UsuarioInDB]:
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def create_usuario(self, db: Session, usuario_in: UsuarioCreate) -> UsuarioInDB:
        # Verificar si el usuario ya existe
        if self.repository.get_by_username(db, usuario_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está registrado"
            )
        
        if self.repository.get_by_email(db, usuario_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        return self.repository.create(db, obj_in=usuario_in)

    def update_usuario(self, db: Session, usuario_id: int, usuario_in: UsuarioUpdate) -> UsuarioInDB:
        usuario = self.repository.get(db, usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return self.repository.update(db, db_obj=usuario, obj_in=usuario_in)

    def delete_usuario(self, db: Session, usuario_id: int) -> UsuarioInDB:
        usuario = self.repository.get(db, usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return self.repository.remove(db, id=usuario_id)

    def get_usuario_by_email(self, db: Session, email: str) -> Optional[UsuarioInDB]:
        return self.repository.get_by_email(db, email)

    def get_usuario_by_username(self, db: Session, username: str) -> Optional[UsuarioInDB]:
        return self.repository.get_by_username(db, username)

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[UsuarioInDB]:
        return self.repository.authenticate(db, username, password)

usuario_service = UsuarioService()