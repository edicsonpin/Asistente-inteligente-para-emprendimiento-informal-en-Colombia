# schemas/oportunidades.py
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from .base import ModeloBase

class TipoOportunidadEnum(str, Enum):
    CREDITO = "CREDITO"
    INVERSION = "INVERSION"
    CAPACITACION = "CAPACITACION"
    NETWORKING = "NETWORKING"
    MENTORIA = "MENTORIA"
    INCUBACION = "INCUBACION"
    CONCURSO = "CONCURSO"
    FONDO_NO_REEMBOLSABLE = "FONDO_NO_REEMBOLSABLE"

class EstadoOportunidadEnum(str, Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"
    PAUSADA = "PAUSADA"
    AGOTADA = "AGOTADA"

class NivelEducacionEnum(str, Enum):
    SIN_EDUCACION = "SIN_EDUCACION"
    PRIMARIA = "PRIMARIA"
    SECUNDARIA = "SECUNDARIA"
    TECNICO = "TECNICO"
    UNIVERSITARIO = "UNIVERSITARIO"
    POSTGRADO = "POSTGRADO"

class OportunidadBase(ModeloBase):
    nombre: str = Field(..., min_length=5, max_length=255, description="Nombre de la oportunidad")
    tipo: TipoOportunidadEnum = Field(..., description="Tipo de oportunidad")
    descripcion: str = Field(..., min_length=10, description="Descripción detallada")
    beneficios: Optional[str] = Field(None, description="Beneficios específicos")
    requisitos: Optional[str] = Field(None, description="Requisitos para aplicar")
    sector_compatible: Optional[str] = Field(None, description="Sector de negocio compatible")
    riesgo_minimo: Optional[str] = Field(None, description="Riesgo mínimo aceptable")
    riesgo_maximo: Optional[str] = Field(None, description="Riesgo máximo aceptable")
    experiencia_minima: int = Field(0, ge=0, description="Experiencia mínima en años")
    empleados_minimos: int = Field(0, ge=0, description="Empleados mínimos requeridos")
    ingresos_minimos: Decimal = Field(0.0, ge=0.0, description="Ingresos mínimos requeridos")
    capital_minimo: Decimal = Field(0.0, ge=0.0, description="Capital mínimo requerido")
    nivel_educacion_minimo: Optional[NivelEducacionEnum] = Field(None, description="Nivel educación mínimo")
    monto_minimo: Decimal = Field(0.0, ge=0.0, description="Monto mínimo ofrecido")
    monto_maximo: Decimal = Field(0.0, ge=0.0, description="Monto máximo ofrecido")
    tasa_interes: Optional[Decimal] = Field(None, ge=0.0, description="Tasa de interés (si aplica)")
    plazo_maximo: Optional[int] = Field(None, ge=0, description="Plazo máximo en meses")
    garantias_requeridas: Optional[str] = Field(None, description="Garantías requeridas")
    fecha_apertura: Optional[datetime] = Field(None, description="Fecha de apertura")
    fecha_cierre: Optional[datetime] = Field(None, description="Fecha de cierre")
    contacto_nombre: Optional[str] = Field(None, max_length=255, description="Nombre de contacto")
    contacto_email: Optional[str] = Field(None, max_length=255, description="Email de contacto")
    contacto_telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    url_aplicacion: Optional[str] = Field(None, max_length=500, description="URL para aplicación")
    estado: EstadoOportunidadEnum = Field(default=EstadoOportunidadEnum.ACTIVA, description="Estado actual")

    @model_validator(mode='after')
    def validar_fechas(self) -> 'OportunidadBase':
        if self.fecha_apertura and self.fecha_cierre:
            if self.fecha_cierre <= self.fecha_apertura:
                raise ValueError('La fecha de cierre debe ser posterior a la fecha de apertura')
        return self

    @model_validator(mode='after')
    def validar_montos(self) -> 'OportunidadBase':
        if float(self.monto_maximo) < float(self.monto_minimo):
            raise ValueError('El monto máximo no puede ser menor al monto mínimo')
        return self

    @field_validator('contacto_email')
    @classmethod
    def validar_email_contacto(cls, v: Optional[str]) -> Optional[str]:
        if v and '@' not in v:
            raise ValueError('Formato de email de contacto inválido')
        return v

class OportunidadCreate(OportunidadBase):
    institucion_id: int = Field(..., gt=0, description="ID de la institución oferente")

class OportunidadUpdate(ModeloBase):
    nombre: Optional[str] = Field(None, min_length=5, max_length=255)
    tipo: Optional[TipoOportunidadEnum] = None
    descripcion: Optional[str] = Field(None, min_length=10)
    beneficios: Optional[str] = None
    requisitos: Optional[str] = None
    sector_compatible: Optional[str] = None
    riesgo_minimo: Optional[str] = None
    riesgo_maximo: Optional[str] = None
    experiencia_minima: Optional[int] = Field(None, ge=0)
    empleados_minimos: Optional[int] = Field(None, ge=0)
    ingresos_minimos: Optional[Decimal] = Field(None, ge=0.0)
    capital_minimo: Optional[Decimal] = Field(None, ge=0.0)
    nivel_educacion_minimo: Optional[NivelEducacionEnum] = None
    monto_minimo: Optional[Decimal] = Field(None, ge=0.0)
    monto_maximo: Optional[Decimal] = Field(None, ge=0.0)
    tasa_interes: Optional[Decimal] = Field(None, ge=0.0)
    plazo_maximo: Optional[int] = Field(None, ge=0)
    garantias_requeridas: Optional[str] = None
    fecha_apertura: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    contacto_nombre: Optional[str] = Field(None, max_length=255)
    contacto_email: Optional[str] = Field(None, max_length=255)
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    url_aplicacion: Optional[str] = Field(None, max_length=500)
    estado: Optional[EstadoOportunidadEnum] = None

class OportunidadInDB(OportunidadBase):
    id: int = Field(..., description="ID único de la oportunidad")
    institucion_id: int = Field(..., description="ID de la institución")
    fecha_publicacion: datetime = Field(..., description="Fecha de publicación")
    puntaje_similitud_base: float = Field(0.0, ge=0.0, le=1.0, description="Puntaje base de similitud")
    popularidad: int = Field(0, ge=0, description="Índice de popularidad")
    vistas: int = Field(0, ge=0, description="Número de vistas")
    aplicaciones_exitosas: int = Field(0, ge=0, description="Aplicaciones exitosas")

class OportunidadConInstitucion(OportunidadInDB):
    institucion: 'InstitucionInDB' = Field(..., description="Información de la institución")

class OportunidadConEstadisticas(OportunidadInDB):
    total_interacciones: int = Field(0, description="Total de interacciones")
    total_aplicaciones: int = Field(0, description="Total de aplicaciones")
    tasa_conversion: float = Field(0.0, ge=0.0, le=100.0, description="Tasa de conversión")
    tiempo_promedio_vista: float = Field(0.0, description="Tiempo promedio de vista en segundos")
    satisfaccion_promedio: Optional[float] = Field(None, ge=0.0, le=5.0, description="Satisfacción promedio")

class CriteriosBusqueda(ModeloBase):
    sector: Optional[str] = Field(None, description="Sector de negocio")
    tipo: Optional[TipoOportunidadEnum] = Field(None, description="Tipo de oportunidad")
    riesgo_minimo: Optional[str] = Field(None, description="Riesgo mínimo aceptable")
    riesgo_maximo: Optional[str] = Field(None, description="Riesgo máximo aceptable")
    experiencia_minima: Optional[int] = Field(None, ge=0, description="Experiencia mínima")
    ingresos_minimos: Optional[Decimal] = Field(None, ge=0.0, description="Ingresos mínimos")
    monto_minimo: Optional[Decimal] = Field(None, ge=0.0, description="Monto mínimo")
    monto_maximo: Optional[Decimal] = Field(None, ge=0.0, description="Monto máximo")
    solo_activas: bool = Field(True, description="Solo oportunidades activas")
    institucion_id: Optional[int] = Field(None, gt=0, description="Filtrar por institución")

class RecomendacionOportunidad(ModeloBase):
    oportunidad: OportunidadConInstitucion = Field(..., description="Oportunidad recomendada")
    puntaje_final: float = Field(..., ge=0.0, le=100.0, description="Puntaje final de recomendación")
    puntaje_contenido: Optional[float] = Field(None, ge=0.0, le=100.0, description="Puntaje de contenido")
    puntaje_colaborativo: Optional[float] = Field(None, ge=0.0, le=100.0, description="Puntaje colaborativo")
    puntaje_conocimiento: Optional[float] = Field(None, ge=0.0, le=100.0, description="Puntaje de conocimiento")
    explicacion: Optional[str] = Field(None, description="Explicación de la recomendación")
    caracteristicas_compatibles: List[str] = Field(..., description="Características compatibles")
    confianza_recomendacion: float = Field(..., ge=0.0, le=1.0, description="Confianza en la recomendación")

class AplicacionOportunidadCreate(ModeloBase):
    negocio_id: int = Field(..., gt=0, description="ID del negocio que aplica")
    oportunidad_id: int = Field(..., gt=0, description="ID de la oportunidad")
    monto_solicitado: Optional[Decimal] = Field(None, ge=0.0, description="Monto solicitado")
    comentarios: Optional[str] = Field(None, description="Comentarios adicionales")
    documentos_adjuntos: Optional[List[Dict[str, str]]] = Field(None, description="Documentos adjuntos")

class AplicacionOportunidadInDB(ModeloBase):
    id: int = Field(..., description="ID único de la aplicación")
    negocio_id: int = Field(..., description="ID del negocio")
    oportunidad_id: int = Field(..., description="ID de la oportunidad")
    estado: str = Field(..., description="Estado de la aplicación")
    fecha_aplicacion: datetime = Field(..., description="Fecha de aplicación")
    fecha_decision: Optional[datetime] = Field(None, description="Fecha de decisión")
    monto_solicitado: Optional[Decimal] = Field(None, description="Monto solicitado")
    monto_aprobado: Optional[Decimal] = Field(None, description="Monto aprobado")
    comentarios: Optional[str] = Field(None, description="Comentarios")
    documentos_adjuntos: Optional[Dict[str, Any]] = Field(None, description="Documentos adjuntos")
    puntaje_evaluacion: Optional[float] = Field(None, description="Puntaje de evaluación")

class FiltroOportunidades(ModeloBase):
    institucion_id: Optional[int] = Field(None, gt=0, description="Filtrar por institución")
    tipo: Optional[TipoOportunidadEnum] = Field(None, description="Filtrar por tipo")
    sector: Optional[str] = Field(None, description="Filtrar por sector")
    estado: Optional[EstadoOportunidadEnum] = Field(None, description="Filtrar por estado")
    fecha_cierre_desde: Optional[datetime] = Field(None, description="Fecha cierre desde")
    fecha_cierre_hasta: Optional[datetime] = Field(None, description="Fecha cierre hasta")
    solo_activas: bool = Field(True, description="Solo oportunidades activas")
    skip: int = Field(0, ge=0, description="Registros a omitir")
    limit: int = Field(100, ge=1, le=1000, description="Límite de registros")

# Importaciones circulares
from schemas.sistema import InstitucionInDB

# Rebuild models
OportunidadConInstitucion.model_rebuild()
RecomendacionOportunidad.model_rebuild()