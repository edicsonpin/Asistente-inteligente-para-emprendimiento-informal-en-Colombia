# repositories/permisos.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import Permiso, Rol
from schemas.roles import PermisoCreate, PermisoUpdate
from repositories.base import CRUDBase

class PermisoRepository(CRUDBase[Permiso, PermisoCreate, PermisoUpdate]):
    def __init__(self):
        super().__init__(Permiso)

    def get_by_modulo_accion(self, db: Session, modulo: str, accion: str) -> Optional[Permiso]:
        return db.query(Permiso).filter(
            Permiso.modulo == modulo,
            Permiso.accion == accion
        ).first()

    def get_by_rol(self, db: Session, rol_id: int) -> List[Permiso]:
        return db.query(Permiso).filter(Permiso.rol_id == rol_id).all()

    def get_permisos_por_modulo(self, db: Session, modulo: str) -> List[Permiso]:
        return db.query(Permiso).filter(Permiso.modulo == modulo).all()

    def create(self, db: Session, *, obj_in: PermisoCreate) -> Permiso:
        # Verificar que el rol existe
        rol = db.query(Rol).filter(Rol.rol_id == obj_in.rol_id).first()
        if not rol:
            raise ValueError("El rol especificado no existe")

        # Verificar que no existe un permiso duplicado
        existente = self.get_by_modulo_accion(db, obj_in.modulo, obj_in.accion)
        if existente:
            raise ValueError("Ya existe un permiso con el mismo módulo y acción")

        db_obj = Permiso(
            rol_id=obj_in.rol_id,
            modulo=obj_in.modulo,
            accion=obj_in.accion,
            descripcion=obj_in.descripcion
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Permiso, obj_in: PermisoUpdate) -> Permiso:
        update_data = obj_in.dict(exclude_unset=True)
        
        # Si se actualiza módulo o acción, verificar duplicados
        if ('modulo' in update_data or 'accion' in update_data):
            nuevo_modulo = update_data.get('modulo', db_obj.modulo)
            nueva_accion = update_data.get('accion', db_obj.accion)
            
            existente = self.get_by_modulo_accion(db, nuevo_modulo, nueva_accion)
            if existente and existente.permiso_id != db_obj.permiso_id:
                raise ValueError("Ya existe un permiso con el mismo módulo y acción")

        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_permisos_activos(self, db: Session) -> List[Permiso]:
        return db.query(Permiso).join(Rol).filter(Rol.activo == True).all()

    def contar_permisos_por_rol(self, db: Session, rol_id: int) -> int:
        return db.query(Permiso).filter(Permiso.rol_id == rol_id).count()

permiso_repository = PermisoRepository()