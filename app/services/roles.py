from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.repositories.roles import rol_repository
from app.schemas.roles import (
    RolCreate, RolUpdate, RolResponse, RolWithPermisos, 
    RolWithUsuarios, PermisoCreate, PermisoUpdate, PermisoResponse
)

class RolService:
    @staticmethod
    def get_rol(db: Session, rol_id: int) -> Optional[RolResponse]:
        rol = rol_repository.get(db, id=rol_id)
        if rol:
            return RolResponse.from_orm(rol)
        return None

    @staticmethod
    def get_rol_with_permisos(db: Session, rol_id: int) -> Optional[RolWithPermisos]:
        rol = rol_repository.get_with_permisos(db, rol_id)
        if rol:
            rol_data = RolWithPermisos.from_orm(rol)
            rol_data.permisos = [f"{permiso.modulo}:{permiso.accion}" for permiso in rol.permisos]
            return rol_data
        return None

    @staticmethod
    def get_rol_with_usuarios(db: Session, rol_id: int) -> Optional[RolWithUsuarios]:
        rol = rol_repository.get_with_usuarios(db, rol_id)
        if rol:
            rol_data = RolWithUsuarios.from_orm(rol)
            rol_data.usuarios_count = len(rol.usuarios)
            rol_data.usuarios = [usuario.username for usuario in rol.usuarios]
            return rol_data
        return None

    @staticmethod
    def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[RolResponse]:
        roles = rol_repository.get_multi(db, skip=skip, limit=limit)
        return [RolResponse.from_orm(rol) for rol in roles]

    @staticmethod
    def get_roles_activos(db: Session, skip: int = 0, limit: int = 100) -> List[RolResponse]:
        roles = rol_repository.get_roles_activos(db, skip=skip, limit=limit)
        return [RolResponse.from_orm(rol) for rol in roles]

    @staticmethod
    def get_roles_by_nivel_permiso(db: Session, nivel_minimo: int, nivel_maximo: int = None) -> List[RolResponse]:
        roles = rol_repository.get_roles_by_nivel_permiso(db, nivel_minimo, nivel_maximo)
        return [RolResponse.from_orm(rol) for rol in roles]

    @staticmethod
    def create_rol(db: Session, rol_in: RolCreate) -> RolResponse:
        rol = rol_repository.create(db, obj_in=rol_in.dict())
        return RolResponse.from_orm(rol)

    @staticmethod
    def update_rol(db: Session, rol_id: int, rol_in: RolUpdate) -> Optional[RolResponse]:
        rol = rol_repository.get(db, id=rol_id)
        if not rol:
            return None
        
        update_data = rol_in.dict(exclude_unset=True)
        rol = rol_repository.update(db, db_obj=rol, obj_in=update_data)
        return RolResponse.from_orm(rol)

    @staticmethod
    def delete_rol(db: Session, rol_id: int) -> bool:
        # Verificar si el rol tiene usuarios asignados
        count_usuarios = rol_repository.contar_usuarios_por_rol(db, rol_id)
        if count_usuarios > 0:
            raise ValueError(f"No se puede eliminar el rol porque tiene {count_usuarios} usuarios asignados")
        
        rol = rol_repository.get(db, id=rol_id)
        if not rol:
            return False
        rol_repository.delete(db, id=rol_id)
        return True

    @staticmethod
    def activar_rol(db: Session, rol_id: int) -> bool:
        rol = rol_repository.get(db, id=rol_id)
        if not rol:
            return False
        
        rol.activo = True
        db.commit()
        return True

    @staticmethod
    def desactivar_rol(db: Session, rol_id: int) -> bool:
        rol = rol_repository.get(db, id=rol_id)
        if not rol:
            return False
        
        rol.activo = False
        db.commit()
        return True

    # Métodos para gestión de permisos
    @staticmethod
    def get_permisos_by_rol(db: Session, rol_id: int) -> List[PermisoResponse]:
        permisos = rol_repository.get_permisos_by_rol(db, rol_id)
        return [PermisoResponse.from_orm(permiso) for permiso in permisos]

    @staticmethod
    def get_permiso(db: Session, permiso_id: int) -> Optional[PermisoResponse]:
        permiso = rol_repository.get_permiso_by_id(db, permiso_id)
        if permiso:
            return PermisoResponse.from_orm(permiso)
        return None

    @staticmethod
    def add_permiso_to_rol(db: Session, rol_id: int, permiso_in: PermisoCreate) -> PermisoResponse:
        permiso = rol_repository.add_permiso(db, rol_id, permiso_in.dict())
        return PermisoResponse.from_orm(permiso)

    @staticmethod
    def update_permiso(db: Session, permiso_id: int, permiso_in: PermisoUpdate) -> Optional[PermisoResponse]:
        permiso = rol_repository.update_permiso(db, permiso_id, permiso_in.dict(exclude_unset=True))
        if permiso:
            return PermisoResponse.from_orm(permiso)
        return None

    @staticmethod
    def remove_permiso_from_rol(db: Session, permiso_id: int) -> bool:
        return rol_repository.remove_permiso(db, permiso_id)

    @staticmethod
    def verificar_permiso(db: Session, rol_id: int, modulo: str, accion: str) -> bool:
        permisos = rol_repository.get_permisos_by_rol(db, rol_id)
        for permiso in permisos:
            if permiso.modulo == modulo and permiso.accion == accion:
                return True
        return False

rol_service = RolService()