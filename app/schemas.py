from pydantic import BaseModel
from typing import Optional
from typing import List


class EmprendedorBase(BaseModel):
    nombre: str
    telefono: str
    email: str
    nivel_digital: Optional[str] = None


class EmprendedorCreate(EmprendedorBase):
    pass


class Emprendedor(EmprendedorBase):
    emprendedor_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class Rol(RolBase):
    rol_id: int

    class Config:
        from_attributes = True 

class User(UserBase):
    id: int
    roles: List[Rol] = []
    class Config:
        from_attributes = True
