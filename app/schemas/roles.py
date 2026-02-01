# schemas/roles.py - VERSIÓN COMPLETA
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from .base import ModeloBase

class PermisoBase(ModeloBase):
    modulo: str = Field(..., max_length=100, description="Módulo del sistema")
    accion: str = Field(..., max_length=100, description="Acción permitida")
    descripcion: Optional[str] = Field(None, description="Descripción del permiso")

class PermisoCreate(PermisoBase):
    pass

class PermisoUpdate(PermisoBase):
    modulo: Optional[str] = None
    accion: Optional[str] = None

class PermisoInDB(PermisoBase):
    permiso_id: int = Field(..., description="ID único del permiso")
    rol_id: int = Field(..., description="ID del rol al que pertenece")
    fecha_creacion: Optional[datetime] = None

class RolBase(ModeloBase):
    nombre: str = Field(..., max_length=100, description="Nombre del rol")
    descripcion: Optional[str] = Field(None, description="Descripción del rol")
    nivel_permiso: int = Field(1, ge=1, le=10, description="Nivel de permiso (1-10)")
    activo: bool = Field(True, description="Indica si el rol está activo")

class RolCreate(RolBase):
    pass

class RolUpdate(ModeloBase):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    nivel_permiso: Optional[int] = Field(None, ge=1, le=10)
    activo: Optional[bool] = None

class RolInDB(RolBase):
    rol_id: int = Field(..., description="ID único del rol")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    permisos: List[PermisoInDB] = []

class RolConUsuarios(RolInDB):
    total_usuarios: int = 0

# ===== NUEVOS SCHEMAS PARA TU ROUTER =====

# Schema base para respuestas
class ResponseBase(ModeloBase):
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje de respuesta")
    
# Schema para rol individual
class RolResponse(RolInDB):
    """Schema para respuesta de rol individual"""
    pass

class RolSingleResponse(ResponseBase):
    """Respuesta estandarizada para un solo rol"""
    data: Optional[RolResponse] = None

class RolesListResponse(ResponseBase):
    """Respuesta estandarizada para lista de roles"""
    data: List[RolResponse] = []

# Schema para rol con permisos
class RolWithPermisos(RolInDB):
    """Rol con lista completa de permisos"""
    permisos_detallados: List[PermisoInDB] = Field(default_factory=list)

class RolWithPermisosResponse(ResponseBase):
    """Respuesta estandarizada para rol con permisos"""
    data: Optional[RolWithPermisos] = None

# Schema para rol con usuarios
class RolWithUsuarios(RolInDB):
    """Rol con información de usuarios"""
    usuarios_count: int = Field(0, description="Número de usuarios con este rol")
    usuarios: List[Any] = Field(default_factory=list, description="Lista de usuarios")

class RolWithUsuariosResponse(ResponseBase):
    """Respuesta estandarizada para rol con usuarios"""
    data: Optional[RolWithUsuarios] = None

# Schemas para permisos
class PermisoResponse(PermisoInDB):
    """Schema para respuesta de permiso individual"""
    pass

class PermisoSingleResponse(ResponseBase):
    """Respuesta estandarizada para un solo permiso"""
    data: Optional[PermisoResponse] = None

class PermisosListResponse(ResponseBase):
    """Respuesta estandarizada para lista de permisos"""
    data: List[PermisoResponse] = []

class AsignacionRol(ModeloBase):
    usuario_id: int = Field(..., description="ID del usuario")
    rol_id: int = Field(..., description="ID del rol")

class CreacionRolCompleto(ModeloBase):
    rol: RolCreate
