# schemas/sistema.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re
from .base import ModeloBase

class NivelLogEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class PaisBase(ModeloBase):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del país")
    codigo_iso: Optional[str] = Field(None, pattern=r'^[A-Z]{2,3}$', description="Código ISO del país")
    emoji: Optional[str] = Field(None, max_length=10, description="Emoji de la bandera")

class PaisCreate(PaisBase):
    pass

class PaisInDB(PaisBase):
    pais_id: int = Field(..., description="ID único del país")

class DepartamentoBase(ModeloBase):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del departamento")

class DepartamentoCreate(DepartamentoBase):
    pais_id: int = Field(..., gt=0, description="ID del país")

class DepartamentoInDB(DepartamentoBase):
    departamento_id: int = Field(..., description="ID único del departamento")
    pais_id: int = Field(..., description="ID del país")

class CiudadBase(ModeloBase):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre de la ciudad")
    latitud: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitud geográfica")
    longitud: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitud geográfica")

class CiudadCreate(CiudadBase):
    departamento_id: int = Field(..., gt=0, description="ID del departamento")

class CiudadInDB(CiudadBase):
    ciudad_id: int = Field(..., description="ID único de la ciudad")
    departamento_id: int = Field(..., description="ID del departamento")

class BarrioBase(ModeloBase):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del barrio")
    latitud: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitud geográfica")
    longitud: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitud geográfica")

class BarrioCreate(BarrioBase):
    ciudad_id: int = Field(..., gt=0, description="ID de la ciudad")

class BarrioInDB(BarrioBase):
    barrio_id: int = Field(..., description="ID único del barrio")
    ciudad_id: int = Field(..., description="ID de la ciudad")

class InstitucionBase(ModeloBase):
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre de la institución")
    tipo: Optional[str] = Field(None, max_length=100, description="Tipo de institución")
    descripcion: Optional[str] = Field(None, description="Descripción de la institución")
    telefono_contacto: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email_contacto: Optional[str] = Field(None, max_length=255, description="Email de contacto")
    persona_contacto: Optional[str] = Field(None, max_length=255, description="Persona de contacto")
    direccion: Optional[str] = Field(None, description="Dirección física")
    website: Optional[str] = Field(None, max_length=500, description="Sitio web")
    activo: bool = Field(True, description="Institución activa")

    @field_validator('email_contacto')
    @classmethod
    def validar_email_institucion(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Formato de email institucional inválido')
        return v

    @field_validator('website')
    @classmethod
    def validar_website_institucion(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
            raise ValueError('Formato de sitio web inválido')
        return v

class InstitucionCreate(InstitucionBase):
    usuario_id: int = Field(..., gt=0, description="ID del usuario asociado")
    pais_id: Optional[int] = Field(None, gt=0, description="ID del país")
    ciudad_id: Optional[int] = Field(None, gt=0, description="ID de la ciudad")

class InstitucionUpdate(ModeloBase):
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    tipo: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    telefono_contacto: Optional[str] = Field(None, max_length=20)
    email_contacto: Optional[str] = Field(None, max_length=255)
    persona_contacto: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    activo: Optional[bool] = None
    pais_id: Optional[int] = Field(None, gt=0)
    ciudad_id: Optional[int] = Field(None, gt=0)

class InstitucionInDB(InstitucionBase):
    id: int = Field(..., description="ID único de la institución")
    usuario_id: int = Field(..., description="ID del usuario")
    pais_id: Optional[int] = Field(None, description="ID del país")
    ciudad_id: Optional[int] = Field(None, description="ID de la ciudad")
    fecha_registro: datetime = Field(..., description="Fecha de registro")

class ConfiguracionSistemaBase(ModeloBase):
    clave: str = Field(..., min_length=3, max_length=100, description="Clave única de configuración")
    valor: str = Field(..., description="Valor de la configuración")
    tipo: str = Field(..., max_length=50, description="Tipo de dato (STRING, NUMBER, BOOLEAN, JSON)")
    descripcion: Optional[str] = Field(None, description="Descripción de la configuración")
    categoria: Optional[str] = Field(None, max_length=100, description="Categoría de la configuración")

class ConfiguracionSistemaCreate(ConfiguracionSistemaBase):
    pass

class ConfiguracionSistemaUpdate(ModeloBase):
    valor: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None

class ConfiguracionSistemaInDB(ConfiguracionSistemaBase):
    id: int = Field(..., description="ID único de la configuración")
    fecha_actualizacion: datetime = Field(..., description="Última actualización")
    usuario_actualizacion: Optional[str] = Field(None, max_length=100, description="Usuario que actualizó")

class CaracteristicaSistemaBase(ModeloBase):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la característica")
    descripcion: Optional[str] = Field(None, description="Descripción de la característica")
    tipo_dato: Optional[str] = Field(None, max_length=50, description="Tipo de dato")
    importancia_global: Optional[float] = Field(None, ge=0.0, le=1.0, description="Importancia global")
    rango_minimo: Optional[float] = Field(None, description="Valor mínimo esperado")
    rango_maximo: Optional[float] = Field(None, description="Valor máximo esperado")
    activa: bool = Field(True, description="Característica activa")

class CaracteristicaSistemaCreate(CaracteristicaSistemaBase):
    pass

class CaracteristicaSistemaInDB(CaracteristicaSistemaBase):
    id: int = Field(..., description="ID único de la característica")
    fecha_actualizacion: datetime = Field(..., description="Última actualización")

class LogSistemaBase(ModeloBase):
    nivel: NivelLogEnum = Field(..., description="Nivel del log")
    modulo: str = Field(..., max_length=100, description="Módulo que generó el log")
    mensaje: str = Field(..., description="Mensaje del log")
    datos_adicionales: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales")
    usuario_id: Optional[int] = Field(None, description="ID del usuario relacionado")
    ip_address: Optional[str] = Field(None, max_length=45, description="Dirección IP")
    user_agent: Optional[str] = Field(None, max_length=500, description="User Agent")

class LogSistemaCreate(LogSistemaBase):
    pass

class LogSistemaInDB(LogSistemaBase):
    id: int = Field(..., description="ID único del log")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")

class AuditoriaBase(ModeloBase):
    usuario_id: Optional[int] = Field(None, description="ID del usuario que realizó la acción")
    accion: str = Field(..., max_length=100, description="Acción realizada")
    modulo: str = Field(..., max_length=100, description="Módulo donde se realizó la acción")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    ip_address: Optional[str] = Field(None, max_length=45, description="Dirección IP")
    user_agent: Optional[str] = Field(None, max_length=500, description="User Agent")
    datos_antes: Optional[Dict[str, Any]] = Field(None, description="Datos antes del cambio")
    datos_despues: Optional[Dict[str, Any]] = Field(None, description="Datos después del cambio")

class AuditoriaCreate(AuditoriaBase):
    pass

class AuditoriaInDB(AuditoriaBase):
    auditoria_id: int = Field(..., description="ID único de la auditoría")
    fecha_evento: datetime = Field(..., description="Fecha del evento")

class UbicacionCompleta(ModeloBase):
    pais: Optional[PaisInDB] = Field(None, description="Información del país")
    departamento: Optional[DepartamentoInDB] = Field(None, description="Información del departamento")
    ciudad: Optional[CiudadInDB] = Field(None, description="Información de la ciudad")
    barrio: Optional[BarrioInDB] = Field(None, description="Información del barrio")

class EstadisticasSistema(ModeloBase):
    total_usuarios: int = Field(0, description="Total de usuarios registrados")
    total_emprendedores: int = Field(0, description="Total de emprendedores")
    total_negocios: int = Field(0, description="Total de negocios")
    total_oportunidades: int = Field(0, description="Total de oportunidades")
    total_evaluaciones: int = Field(0, description="Total de evaluaciones")
    tasa_crecimiento_usuarios: float = Field(0.0, description="Tasa de crecimiento de usuarios (%)")
    distribucion_sectores: Dict[str, int] = Field(..., description="Distribución por sectores")
    distribucion_riesgo: Dict[str, int] = Field(..., description="Distribución por categorías de riesgo")
    oportunidades_activas: int = Field(0, description="Oportunidades activas")
    tasa_exito_oportunidades: float = Field(0.0, description="Tasa de éxito en oportunidades (%)")
    accuracy_sistema: float = Field(0.0, description="Accuracy promedio del sistema")

    @field_validator('tasa_crecimiento_usuarios', 'tasa_exito_oportunidades', 'accuracy_sistema')
    @classmethod
    def validar_porcentajes(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError('Los porcentajes deben estar entre 0 y 100')
        return v