from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.repositories.usuarios import usuario_repository
from app.schemas.usuarios import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, 
    UsuarioWithRoles, UsuarioResetPassword, UsuarioUpdatePassword
)
from app.core.security import verify_password

class UsuarioService:
    @staticmethod
    def get_usuario(db: Session, usuario_id: int) -> Optional[UsuarioResponse]:
        usuario = usuario_repository.get(db, id=usuario_id)
        if usuario:
            return UsuarioResponse.from_orm(usuario)
        return None

    @staticmethod
    def get_usuario_with_roles(db: Session, usuario_id: int) -> Optional[UsuarioWithRoles]:
        usuario = usuario_repository.get_with_roles(db, usuario_id)
        if usuario:
            usuario_data = UsuarioWithRoles.from_orm(usuario)
            usuario_data.roles = [rol.nombre for rol in usuario.roles]
            return usuario_data
        return None

    @staticmethod
    def get_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        usuarios = usuario_repository.get_multi(db, skip=skip, limit=limit)
        return [UsuarioResponse.from_orm(usuario) for usuario in usuarios]

    @staticmethod
    def get_usuarios_by_tipo(db: Session, tipo_usuario: str, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        usuarios = usuario_repository.get_usuarios_by_tipo(db, tipo_usuario, skip=skip, limit=limit)
        return [UsuarioResponse.from_orm(usuario) for usuario in usuarios]

    @staticmethod
    def create_usuario(db: Session, usuario_in: UsuarioCreate) -> UsuarioResponse:
        usuario = usuario_repository.create(db, obj_in=usuario_in)
        return UsuarioResponse.from_orm(usuario)

    @staticmethod
    def update_usuario(db: Session, usuario_id: int, usuario_in: UsuarioUpdate) -> Optional[UsuarioResponse]:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return None
        
        update_data = usuario_in.dict(exclude_unset=True)
        usuario = usuario_repository.update(db, db_obj=usuario, obj_in=update_data)
        return UsuarioResponse.from_orm(usuario)

    @staticmethod
    def update_password(db: Session, usuario_id: int, password_data: UsuarioUpdatePassword) -> bool:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return False
        
        if not verify_password(password_data.current_password, usuario.password_hash):
            return False
        
        usuario_repository.update_password(db, db_obj=usuario, new_password=password_data.new_password)
        return True

    @staticmethod
    def reset_password(db: Session, usuario_id: int, password_data: UsuarioResetPassword) -> bool:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return False
        
        usuario_repository.update_password(db, db_obj=usuario, new_password=password_data.new_password)
        return True

    @staticmethod
    def delete_usuario(db: Session, usuario_id: int) -> bool:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return False
        usuario_repository.delete(db, id=usuario_id)
        return True

    @staticmethod
    def authenticate_usuario(db: Session, username: str, password: str) -> Optional[UsuarioResponse]:
        usuario = usuario_repository.authenticate(db, username=username, password=password)
        if usuario:
            return UsuarioResponse.from_orm(usuario)
        return None

    @staticmethod
    def bloquear_usuario(db: Session, usuario_id: int) -> bool:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return False
        
        usuario.estado = "BLOQUEADO"
        db.commit()
        return True

    @staticmethod
    def activar_usuario(db: Session, usuario_id: int) -> bool:
        usuario = usuario_repository.get(db, id=usuario_id)
        if not usuario:
            return False
        
        usuario.estado = "ACTIVO"
        usuario.intentos_fallidos = 0
        db.commit()
        return True

    @staticmethod
    def add_rol_to_usuario(db: Session, usuario_id: int, rol_id: int) -> bool:
        return usuario_repository.add_rol(db, usuario_id, rol_id)

    @staticmethod
    def remove_rol_from_usuario(db: Session, usuario_id: int, rol_id: int) -> bool:
        return usuario_repository.remove_rol(db, usuario_id, rol_id)

usuario_service = UsuarioService()