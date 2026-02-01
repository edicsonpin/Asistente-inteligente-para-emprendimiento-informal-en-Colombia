from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

class TipoUsuario(str, Enum):
    EMPRENDEDOR = "EMPRENDEDOR"
    INSTITUCION = "INSTITUCION"
    ADMINISTRADOR = "ADMINISTRADOR"
    CONSULTOR = "CONSULTOR"
    ANALISTA = "ANALISTA"

class EstadoUsuario(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    PENDIENTE = "PENDIENTE"
    BLOQUEADO = "BLOQUEADO"

class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=255)
    tipo_usuario: TipoUsuario
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=255)
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Solo letras, números y guiones bajos')
        return v

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Mínimo 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Al menos un número')
        return v

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=255)
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=255)
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)
    estado: Optional[EstadoUsuario] = Field(None)

class UsuarioInDB(UsuarioBase):
    usuario_id: int = Field(..., description="ID único del usuario")
    estado: EstadoUsuario = Field(..., description="Estado actual del usuario")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del usuario")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización")
    ultimo_login: Optional[datetime] = Field(None, description="Fecha del último login")

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str = Field(..., description="Token de acceso JWT")
    token_type: str = Field(..., description="Tipo de token (bearer)")

class TokenData(BaseModel):
    username: Optional[str] = Field(None, description="Username del usuario")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")

class RolBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)

class RolInDB(RolBase):
    rol_id: int = Field(..., description="ID único del rol")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")

    class Config:
        from_attributes = True

class UsuarioResponse(BaseModel):
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    data: Optional[UsuarioInDB] = Field(None, description="Datos del usuario")
    message: Optional[str] = Field(None, description="Mensaje de respuesta")

    class Config:
        from_attributes = True

class UsuarioListResponse(BaseModel):
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    data: List[UsuarioInDB] = Field(..., description="Lista de usuarios")
    total: int = Field(..., description="Total de usuarios")
    pagina: int = Field(..., description="Página actual")
    por_pagina: int = Field(..., description="Elementos por página")

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    success: bool = Field(..., description="Indica si el login fue exitoso")
    data: Optional[Token] = Field(None, description="Datos del token")
    user: Optional[UsuarioInDB] = Field(None, description="Datos del usuario")
    message: Optional[str] = Field(None, description="Mensaje de respuesta")

class UsuarioFilter(BaseModel):
    tipo_usuario: Optional[TipoUsuario] = Field(None, description="Filtrar por tipo de usuario")
    estado: Optional[EstadoUsuario] = Field(None, description="Filtrar por estado")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    search: Optional[str] = Field(None, description="Búsqueda en nombre/email/username")

class PaginationParams(BaseModel):
    pagina: int = Field(1, ge=1, description="Número de página")
    por_pagina: int = Field(10, ge=1, le=100, description="Elementos por página")
    ordenar_por: Optional[str] = Field("fecha_creacion", description="Campo para ordenar")
    orden: str = Field("desc", pattern="^(asc|desc)$", description="Dirección del orden")