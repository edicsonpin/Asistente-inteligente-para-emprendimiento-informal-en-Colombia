# repositories/usuarios.py
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import Usuario, Rol, Emprendedor, Institucion
from schemas.usuarios import UsuarioCreate, UsuarioUpdate
from repositories.base import CRUDBase
# ✅ Este import está bien - no causa circular
from core.security import get_password_hash, verify_password

class UsuarioRepository(CRUDBase[Usuario, UsuarioCreate, UsuarioUpdate]):
    def __init__(self):
        super().__init__(Usuario)

    def get_by_email(self, db: Session, email: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.email == email).first()

    def get_by_username(self, db: Session, username: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.username == username).first()

    def create(self, db: Session, *, obj_in: UsuarioCreate) -> Usuario:
        # Hash de la contraseña usando core.security
        hashed_password = get_password_hash(obj_in.password)
        
        # Crear usuario sin la contraseña en texto plano
        try:
            user_data = obj_in.model_dump(exclude={'password'})
        except AttributeError:
            user_data = obj_in.dict(exclude={'password'})
        
        user_data['password_hash'] = hashed_password
        
        db_obj = Usuario(**user_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, username: str, password: str) -> Optional[Usuario]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def get_roles(self, db: Session, user_id: int) -> List[Rol]:
        user = self.get(db, user_id)
        return user.roles if user else []

    def add_role(self, db: Session, user_id: int, role_id: int) -> Usuario:
        user = self.get(db, user_id)
        role = db.query(Rol).filter(Rol.rol_id == role_id).first()
        
        if user and role and role not in user.roles:
            user.roles.append(role)
            db.commit()
            db.refresh(user)
        
        return user

    def get_emprendedor(self, db: Session, user_id: int) -> Optional[Emprendedor]:
        user = self.get(db, user_id)
        return user.emprendedor if user else None

    def get_institucion(self, db: Session, user_id: int) -> Optional[Institucion]:
        user = self.get(db, user_id)
        return user.institucion if user else None

    def update_last_login(self, db: Session, user_id: int) -> Usuario:
        user = self.get(db, user_id)
        if user:
            # Actualizar último login (usando SQLAlchemy para timestamp)
            from sqlalchemy import func
            user.ultimo_login = func.now()
            db.commit()
            db.refresh(user)
        return user

usuario_repository = UsuarioRepository()