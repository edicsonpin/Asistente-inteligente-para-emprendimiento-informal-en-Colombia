from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database.models import Rol, Permiso, Usuario
from app.repositories.base import CRUDBase

class RolRepository(CRUDBase):
    def __init__(self):
        super().__init__(Rol)

    def get_by_nombre(self, db: Session, nombre: str) -> Optional[Rol]:
        return db.query(Rol).filter(Rol.nombre == nombre).first()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> Rol:
        # Verificar unicidad del nombre
        if self.get_by_nombre(db, obj_in['nombre']):
            raise ValueError("Ya existe un rol con ese nombre")

        db_obj = Rol(
            nombre=obj_in['nombre'],
            descripcion=obj_in.get('descripcion'),
            nivel_permiso=obj_in.get('nivel_permiso', 1),
            activo=obj_in.get('activo', True)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Rol, obj_in: Dict[str, Any]) -> Rol:
        # Si se está actualizando el nombre, verificar que no exista
        if 'nombre' in obj_in and obj_in['nombre'] != db_obj.nombre:
            if self.get_by_nombre(db, obj_in['nombre']):
                raise ValueError("Ya existe un rol con ese nombre")

        update_data = {k: v for k, v in obj_in.items() if v is not None}
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_with_permisos(self, db: Session, rol_id: int) -> Optional[Rol]:
        return db.query(Rol).filter(Rol.rol_id == rol_id).first()

    def get_with_usuarios(self, db: Session, rol_id: int) -> Optional[Rol]:
        return db.query(Rol).filter(Rol.rol_id == rol_id).first()

    def add_permiso(self, db: Session, rol_id: int, permiso_data: Dict[str, Any]) -> Permiso:
        rol = self.get(db, rol_id)
        if not rol:
            raise ValueError("Rol no encontrado")

        # Verificar si el permiso ya existe
        permiso_existente = db.query(Permiso).filter(
            Permiso.rol_id == rol_id,
            Permiso.modulo == permiso_data['modulo'],
            Permiso.accion == permiso_data['accion']
        ).first()

        if permiso_existente:
            raise ValueError("El permiso ya existe para este rol")
        fecha_creacion: datetime
        permiso = Permiso(
            rol_id=rol_id,
            modulo=permiso_data['modulo'],
            accion=permiso_data['accion'],
            descripcion=permiso_data.get('descripcion')
        )
        db.add(permiso)
        db.commit()
        db.refresh(permiso)
        return permiso

    def update_permiso(self, db: Session, permiso_id: int, permiso_data: Dict[str, Any]) -> Optional[Permiso]:
        permiso = db.query(Permiso).filter(Permiso.permiso_id == permiso_id).first()
        if not permiso:
            return None

        update_data = {k: v for k, v in permiso_data.items() if v is not None}
        for field, value in update_data.items():
            setattr(permiso, field, value)
        
        db.commit()
        db.refresh(permiso)
        return permiso

    def remove_permiso(self, db: Session, permiso_id: int) -> bool:
        permiso = db.query(Permiso).filter(Permiso.permiso_id == permiso_id).first()
        if not permiso:
            return False
        
        db.delete(permiso)
        db.commit()
        return True

    def get_permisos_by_rol(self, db: Session, rol_id: int) -> List[Permiso]:
        return db.query(Permiso).filter(Permiso.rol_id == rol_id).all()

    def get_permiso_by_id(self, db: Session, permiso_id: int) -> Optional[Permiso]:
        return db.query(Permiso).filter(Permiso.permiso_id == permiso_id).first()

    def get_roles_activos(self, db: Session, skip: int = 0, limit: int = 100) -> List[Rol]:
        return db.query(Rol).filter(Rol.activo == True).offset(skip).limit(limit).all()

    def get_roles_by_nivel_permiso(self, db: Session, nivel_minimo: int, nivel_maximo: int = None) -> List[Rol]:
        query = db.query(Rol).filter(Rol.nivel_permiso >= nivel_minimo)
        if nivel_maximo:
            query = query.filter(Rol.nivel_permiso <= nivel_maximo)
        return query.all()

    def contar_usuarios_por_rol(self, db: Session, rol_id: int) -> int:
        rol = self.get_with_usuarios(db, rol_id)
        if not rol:
            return 0
        return len(rol.usuarios)

rol_repository = RolRepository()