# schemas/negocios.py
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
import re
from .base import ModeloBase

class SectorNegocioEnum(str, Enum):
    TECNOLOGIA = "TECNOLOGIA"
    COMERCIO = "COMERCIO"
    SERVICIOS = "SERVICIOS"
    INDUSTRIA = "INDUSTRIA"
    AGRICULTURA = "AGRICULTURA"
    CONSTRUCCION = "CONSTRUCCION"
    TRANSPORTE = "TRANSPORTE"
    TURISMO = "TURISMO"
    SALUD = "SALUD"
    EDUCACION = "EDUCACION"
    OTRO = "OTRO"

class EstadoNegocioEnum(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    EN_CREACION = "EN_CREACION"
    VERIFICACION_PENDIENTE = "VERIFICACION_PENDIENTE"
    RECHAZADO = "RECHAZADO"

class TipoDocumentoEnum(str, Enum):
    RUT = "RUT"
    NIT = "NIT"
    CEDULA = "CEDULA"
    PASAPORTE = "PASAPORTE"
    LICENCIA_COMERCIAL = "LICENCIA_COMERCIAL"
    CAMARA_COMERCIO = "CAMARA_COMERCIO"
    OTRO = "OTRO"

class NegocioBase(ModeloBase):
    nombre_comercial: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Nombre comercial público del negocio"
    )
    razon_social: Optional[str] = Field(
        None,
        max_length=255,
        description="Razón social legal (si aplica)"
    )
    es_mipyme: bool = Field(
        default=True,
        description="Clasificación como micro, pequeña o mediana empresa"
    )
    es_negocio_principal: bool = Field(
        default=True,
        description="Indica si es el negocio principal del emprendedor"
    )
    tipo_documento: Optional[TipoDocumentoEnum] = Field(
        None,
        description="Tipo de documento de identificación legal"
    )
    numero_documento: Optional[str] = Field(
        None,
        max_length=100,
        description="Número del documento de identificación"
    )
    fecha_constitucion: Optional[datetime] = Field(
        None,
        description="Fecha de constitución legal del negocio"
    )
    camara_comercio: Optional[str] = Field(
        None,
        max_length=100,
        description="Número de registro en cámara de comercio"
    )
    sector_negocio: SectorNegocioEnum = Field(
        ...,
        description="Sector económico principal del negocio"
    )
    subsector: Optional[str] = Field(
        None,
        max_length=100,
        description="Subsector o nicho específico"
    )
    codigo_ciiu: Optional[str] = Field(
        None,
        max_length=10,
        pattern=r"^\d{4,5}$",
        description="Código CIIU para clasificación de actividades económicas"
    )
    descripcion_actividad: Optional[str] = Field(
        None,
        max_length=1000,
        description="Descripción detallada de la actividad del negocio"
    )
    experiencia_sector: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Años de experiencia específica en el sector"
    )
    meses_operacion: int = Field(
        default=0,
        ge=0,
        description="Meses que el negocio ha estado en operación"
    )
    empleados_directos: int = Field(
        default=0,
        ge=0,
        description="Número de empleados directos"
    )
    empleados_indirectos: int = Field(
        default=0,
        ge=0,
        description="Número de empleados indirectos o contratistas"
    )
    modelo_negocio: Optional[str] = Field(
        None,
        max_length=255,
        description="Modelo de negocio (B2B, B2C, SaaS, etc.)"
    )
    sitio_web: Optional[str] = Field(
        None,
        max_length=500,
        description="Sitio web oficial del negocio"
    )
    ingresos_mensuales_promedio: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Ingresos mensuales promedio en COP"
    )
    ingresos_anuales: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Ingresos anuales totales en COP"
    )
    capital_trabajo: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Capital de trabajo disponible en COP"
    )
    deuda_existente: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Deuda total actual en COP"
    )
    activos_totales: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Valor total de activos en COP"
    )
    pasivos_totales: Decimal = Field(
        default=0.0,
        ge=0.0,
        description="Valor total de pasivos en COP"
    )
    flujo_efectivo_mensual: Decimal = Field(
        default=0.0,
        description="Flujo de efectivo mensual neto en COP"
    )
    direccion_comercial: Optional[str] = Field(
        None,
        max_length=500,
        description="Dirección comercial principal"
    )
    telefono_comercial: Optional[str] = Field(
        None,
        max_length=20,
        description="Teléfono comercial principal"
    )
    email_comercial: Optional[str] = Field(
        None,
        max_length=255,
        description="Email comercial principal"
    )
    persona_contacto: Optional[str] = Field(
        None,
        max_length=255,
        description="Persona de contacto principal"
    )
    estado: EstadoNegocioEnum = Field(
        default=EstadoNegocioEnum.EN_CREACION,
        description="Estado actual del negocio en el sistema"
    )

    @field_validator('nombre_comercial')
    @classmethod
    def validar_nombre_comercial(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('El nombre comercial debe tener al menos 2 caracteres')
        return v.strip()

    @field_validator('email_comercial')
    @classmethod
    def validar_email_comercial(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Formato de email comercial inválido')
        return v

    @field_validator('telefono_comercial')
    @classmethod
    def validar_telefono_comercial(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[\d\s\-\+\(\)]{7,20}$', v):
            raise ValueError('Formato de teléfono comercial inválido')
        return v

    @field_validator('sitio_web')
    @classmethod
    def validar_sitio_web(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
            raise ValueError('Formato de sitio web inválido')
        return v

    @model_validator(mode='after')
    def validar_consistencia_financiera(self) -> 'NegocioBase':
        # Validar que los ingresos anuales sean consistentes con mensuales
        if (self.ingresos_anuales > 0 and self.ingresos_mensuales_promedio > 0 and
            abs(float(self.ingresos_anuales) - float(self.ingresos_mensuales_promedio * 12)) > float(self.ingresos_anuales) * 0.2):
            raise ValueError('Los ingresos anuales no son consistentes con los ingresos mensuales promedio')
        
        # Validar que activos >= pasivos
        if float(self.activos_totales) < float(self.pasivos_totales):
            raise ValueError('Los activos totales no pueden ser menores que los pasivos totales')
        
        return self

class NegocioCreate(NegocioBase):
    emprendedor_id: int = Field(..., gt=0, description="ID del emprendedor propietario")
    pais_id: Optional[int] = Field(None, gt=0, description="ID del país donde opera")
    ciudad_id: Optional[int] = Field(None, gt=0, description="ID de la ciudad donde opera")
    barrio_id: Optional[int] = Field(None, gt=0, description="ID del barrio donde opera")

class NegocioUpdate(ModeloBase):
    nombre_comercial: Optional[str] = Field(None, min_length=2, max_length=255)
    razon_social: Optional[str] = Field(None, max_length=255)
    es_mipyme: Optional[bool] = None
    es_negocio_principal: Optional[bool] = None
    tipo_documento: Optional[TipoDocumentoEnum] = None
    numero_documento: Optional[str] = Field(None, max_length=100)
    fecha_constitucion: Optional[datetime] = None
    camara_comercio: Optional[str] = Field(None, max_length=100)
    sector_negocio: Optional[SectorNegocioEnum] = None
    subsector: Optional[str] = Field(None, max_length=100)
    codigo_ciiu: Optional[str] = Field(None, max_length=10)
    descripcion_actividad: Optional[str] = Field(None, max_length=1000)
    experiencia_sector: Optional[int] = Field(None, ge=0, le=50)
    meses_operacion: Optional[int] = Field(None, ge=0)
    empleados_directos: Optional[int] = Field(None, ge=0)
    empleados_indirectos: Optional[int] = Field(None, ge=0)
    modelo_negocio: Optional[str] = Field(None, max_length=255)
    sitio_web: Optional[str] = Field(None, max_length=500)
    ingresos_mensuales_promedio: Optional[Decimal] = Field(None, ge=0.0)
    ingresos_anuales: Optional[Decimal] = Field(None, ge=0.0)
    capital_trabajo: Optional[Decimal] = Field(None, ge=0.0)
    deuda_existente: Optional[Decimal] = Field(None, ge=0.0)
    activos_totales: Optional[Decimal] = Field(None, ge=0.0)
    pasivos_totales: Optional[Decimal] = Field(None, ge=0.0)
    flujo_efectivo_mensual: Optional[Decimal] = Field(None)
    direccion_comercial: Optional[str] = Field(None, max_length=500)
    telefono_comercial: Optional[str] = Field(None, max_length=20)
    email_comercial: Optional[str] = Field(None, max_length=255)
    persona_contacto: Optional[str] = Field(None, max_length=255)
    estado: Optional[EstadoNegocioEnum] = None
    pais_id: Optional[int] = Field(None, gt=0)
    ciudad_id: Optional[int] = Field(None, gt=0)
    barrio_id: Optional[int] = Field(None, gt=0)

class NegocioInDB(NegocioBase):
    id: int = Field(..., description="ID único del negocio")
    emprendedor_id: int = Field(..., description="ID del emprendedor propietario")
    pais_id: Optional[int] = Field(None, description="ID del país")
    ciudad_id: Optional[int] = Field(None, description="ID de la ciudad")
    barrio_id: Optional[int] = Field(None, description="ID del barrio")
    usuario_verificacion: Optional[int] = Field(None, description="ID del usuario que verificó")
    fecha_registro: datetime = Field(..., description="Fecha de registro")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última actualización")
    fecha_verificacion: Optional[datetime] = Field(None, description="Fecha de verificación")
    edad_negocio: Optional[int] = Field(None, description="Edad en meses calculada")
    ratio_deuda_ingresos: Optional[float] = Field(None, ge=0.0, description="Ratio deuda/ingresos")
    rentabilidad_estimada: Optional[float] = Field(None, description="Rentabilidad estimada")
    puntaje_credito_negocio: Optional[int] = Field(None, ge=0, le=1000, description="Puntaje de crédito")
    calificacion_riesgo_negocio: Optional[str] = Field(None, description="Calificación de riesgo")

class NegocioConEmprendedor(NegocioInDB):
    emprendedor: 'EmprendedorInDB' = Field(..., description="Información del emprendedor propietario")

class NegocioConUbicacion(NegocioInDB):
    pais: Optional['PaisInDB'] = Field(None, description="Información del país")
    ciudad: Optional['CiudadInDB'] = Field(None, description="Información de la ciudad")
    barrio: Optional['BarrioInDB'] = Field(None, description="Información del barrio")

class NegocioConEvaluaciones(NegocioInDB):
    evaluaciones_riesgo: List['EvaluacionRiesgoInDB'] = Field(default_factory=list, description="Historial de evaluaciones")
    ultima_evaluacion: Optional['EvaluacionRiesgoInDB'] = Field(None, description="Evaluación más reciente")

class NegocioCompleto(NegocioConEmprendedor, NegocioConUbicacion, NegocioConEvaluaciones):
    """Schema completo con toda la información del negocio"""
    pass

class MetricasFinancieras(ModeloBase):
    negocio_id: int = Field(..., description="ID del negocio")
    ratio_deuda_ingresos: float = Field(..., ge=0.0, description="Deuda vs Ingresos")
    rentabilidad_estimada: float = Field(..., description="Rentabilidad estimada (%)")
    margen_utilidad: Optional[float] = Field(None, description="Margen de utilidad (%)")
    ratio_endeudamiento: Optional[float] = Field(None, ge=0.0, description="Ratio de endeudamiento")
    liquidez_corriente: Optional[float] = Field(None, ge=0.0, description="Liquidez corriente")
    rotacion_activos: Optional[float] = Field(None, ge=0.0, description="Rotación de activos")
    salud_financiera: str = Field(..., description="EXCELENTE, BUENA, REGULAR, CRITICA")

class EstadisticasNegocio(ModeloBase):
    negocio_id: int = Field(..., description="ID del negocio")
    total_evaluaciones: int = Field(0, description="Total de evaluaciones realizadas")
    empleados_totales: int = Field(0, description="Total de empleados (directos + indirectos)")
    ingresos_mensuales: Decimal = Field(0.0, description="Ingresos mensuales promedio")
    antiguedad_meses: int = Field(0, description="Antigüedad en meses")
    categoria_riesgo_actual: Optional[str] = Field(None, description="Categoría de riesgo actual")
    oportunidades_aplicadas: int = Field(0, description="Oportunidades a las que ha aplicado")
    oportunidades_ganadas: int = Field(0, description="Oportunidades obtenidas")
    tasa_exito: float = Field(0.0, ge=0.0, le=100.0, description="Tasa de éxito en oportunidades")

class FiltroNegocios(ModeloBase):
    emprendedor_id: Optional[int] = Field(None, gt=0, description="Filtrar por emprendedor")
    sector: Optional[SectorNegocioEnum] = Field(None, description="Filtrar por sector")
    estado: Optional[EstadoNegocioEnum] = Field(None, description="Filtrar por estado")
    ciudad_id: Optional[int] = Field(None, gt=0, description="Filtrar por ciudad")
    es_mipyme: Optional[bool] = Field(None, description="Filtrar por clasificación MIPYME")
    ingresos_minimos: Optional[Decimal] = Field(None, ge=0.0, description="Ingresos mínimos")
    ingresos_maximos: Optional[Decimal] = Field(None, ge=0.0, description="Ingresos máximos")
    empleados_minimos: Optional[int] = Field(None, ge=0, description="Empleados mínimos")
    antiguedad_minima: Optional[int] = Field(None, ge=0, description="Antigüedad mínima en meses")
    categoria_riesgo: Optional[str] = Field(None, description="Filtrar por categoría de riesgo")
    skip: int = Field(0, ge=0, description="Registros a omitir")
    limit: int = Field(100, ge=1, le=1000, description="Límite de registros")
    ordenar_por: str = Field("fecha_registro", description="Campo para ordenar")
    orden_descendente: bool = Field(True, description="Orden descendente")

# Importaciones circulares
from schemas.emprendedores import EmprendedorInDB
from schemas.sistema import PaisInDB, CiudadInDB, BarrioInDB
from schemas.evaluaciones import EvaluacionRiesgoInDB

# Rebuild models
NegocioConEmprendedor.model_rebuild()
NegocioConUbicacion.model_rebuild()
NegocioConEvaluaciones.model_rebuild()
NegocioCompleto.model_rebuild()