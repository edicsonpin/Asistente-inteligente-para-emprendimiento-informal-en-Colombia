# schemas/emprendedores.py
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from .base import ModeloBase
import re

class EstadoEmprendedorEnum(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    PENDIENTE = "PENDIENTE"
    RECHAZADO = "RECHAZADO"

class PreferenciaContactoEnum(str, Enum):
    EMAIL = "EMAIL"
    TELEFONO = "TELEFONO"
    WHATSAPP = "WHATSAPP"
    APLICACION = "APLICACION"

class NivelIdiomaEnum(str, Enum):
    BASICO = "BASICO"
    INTERMEDIO = "INTERMEDIO"
    AVANZADO = "AVANZADO"
    NATIVO = "NATIVO"

class EmprendedorBase(ModeloBase):
    biografia: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Biografía profesional del emprendedor, experiencia y background"
    )
    experiencia_total: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Años totales de experiencia profesional en cualquier sector"
    )
    habilidades: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Lista de habilidades técnicas y profesionales (máx. 20)"
    )
    intereses: List[str] = Field(
        default_factory=list,
        max_length=15,
        description="Áreas de interés profesional y sectores de preferencia (máx. 15)"
    )
    linkedin_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL completa del perfil de LinkedIn"
    )
    sitio_web_personal: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Sitio web personal, portafolio o blog profesional"
    )
    direccion_residencia: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Dirección completa de residencia para geolocalización"
    )
    preferencia_contacto: PreferenciaContactoEnum = Field(
        default=PreferenciaContactoEnum.EMAIL,
        description="Método preferido para contactos y notificaciones"
    )
    recibir_notificaciones: bool = Field(
        default=True,
        description="Consentimiento para recibir notificaciones del sistema"
    )
    idiomas: Dict[str, str] = Field(
        default_factory=dict,
        description="Diccionario de idiomas y niveles: {'español': 'NATIVO', 'inglés': 'INTERMEDIO'}"
    )
    estado: EstadoEmprendedorEnum = Field(
        default=EstadoEmprendedorEnum.PENDIENTE,
        description="Estado actual del emprendedor en el proceso de verificación"
    )
    disponibilidad_tiempo: str = Field(
        default="TIEMPO_COMPLETO",
        description="Disponibilidad para dedicar al emprendimiento: TIEMPO_COMPLETO, MEDIO_TIEMPO, FINES_SEMANA"
    )
    nivel_educacion: Optional[str] = Field(
        default=None,
        description="Máximo nivel de educación formal alcanzado"
    )
    redes_sociales: Dict[str, str] = Field(
        default_factory=dict,
        description="Diccionario con enlaces a redes sociales: {'twitter': 'url', 'facebook': 'url'}"
    )

    @field_validator('biografia')
    @classmethod
    def validar_biografia(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) < 10:
            raise ValueError('La biografía debe tener al menos 10 caracteres')
        return v

    @field_validator('habilidades', 'intereses')
    @classmethod
    def validar_listas(cls, v: List[str]) -> List[str]:
        if len(v) > 20:
            raise ValueError('No se pueden tener más de 20 elementos en la lista')
        
        # Validar que no haya elementos duplicados
        unique_items = list(set(v))
        if len(unique_items) != len(v):
            raise ValueError('No se permiten elementos duplicados en la lista')
        
        # Validar longitud de cada elemento
        for item in v:
            if len(item.strip()) < 2:
                raise ValueError('Cada elemento debe tener al menos 2 caracteres')
            if len(item.strip()) > 100:
                raise ValueError('Cada elemento no puede exceder 100 caracteres')
        
        return unique_items

    @field_validator('linkedin_url')
    @classmethod
    def validar_linkedin(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.strip():
            return None
        
        if v:
            linkedin_pattern = r'^https?://(www\.)?linkedin\.com/(in|company)/[a-zA-Z0-9-]+/?$'
            if not re.match(linkedin_pattern, v):
                raise ValueError('URL de LinkedIn inválida. Formato esperado: https://linkedin.com/in/usuario')
        
        return v

    @field_validator('sitio_web_personal')
    @classmethod
    def validar_sitio_web(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.strip():
            return None
        
        if v:
            # Validar formato básico de URL
            url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/\S*)?$'
            if not re.match(url_pattern, v):
                raise ValueError('URL del sitio web inválida. Debe comenzar con http:// o https://')
        
        return v

    @field_validator('idiomas')
    @classmethod
    def validar_idiomas(cls, v: Dict[str, str]) -> Dict[str, str]:
        valid_levels = [level.value for level in NivelIdiomaEnum]
        
        for idioma, nivel in v.items():
            if not idioma.strip():
                raise ValueError('El nombre del idioma no puede estar vacío')
            if nivel not in valid_levels:
                raise ValueError(f'Nivel de idioma inválido. Use: {", ".join(valid_levels)}')
        
        return v

    @field_validator('redes_sociales')
    @classmethod
    def validar_redes_sociales(cls, v: Dict[str, str]) -> Dict[str, str]:
        plataformas_validas = ['twitter', 'facebook', 'instagram', 'youtube', 'tiktok', 'github']
        
        for plataforma, url in v.items():
            if plataforma.lower() not in plataformas_validas:
                raise ValueError(f'Plataforma no soportada: {plataforma}. Use: {", ".join(plataformas_validas)}')
            
            if url and not re.match(r'^https?://[^\s]+$', url):
                raise ValueError(f'URL inválida para {plataforma}')
        
        return v

    @model_validator(mode='after')
    def validar_experiencia_coherente(self) -> 'EmprendedorBase':
        # Validar que la experiencia total sea coherente con la edad típica
        if self.experiencia_total > 40:
            raise ValueError('La experiencia total parece excesiva. Verifique el valor.')
        return self

class EmprendedorCreate(EmprendedorBase):
    usuario_id: int = Field(
        ...,
        gt=0,
        description="ID del usuario asociado al perfil de emprendedor"
    )
    pais_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID del país de residencia actual"
    )
    ciudad_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID de la ciudad de residencia actual"
    )
    barrio_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID del barrio de residencia actual"
    )

    @model_validator(mode='after')
    def validar_ubicacion_completa(self) -> 'EmprendedorCreate':
        # Validar que si se proporciona barrio, también se proporcione ciudad y país
        if self.barrio_residencia_id and not self.ciudad_residencia_id:
            raise ValueError('Si proporciona barrio, debe proporcionar ciudad')
        if self.ciudad_residencia_id and not self.pais_residencia_id:
            raise ValueError('Si proporciona ciudad, debe proporcionar país')
        return self

class EmprendedorUpdate(ModeloBase):
    biografia: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Actualizar biografía profesional"
    )
    experiencia_total: Optional[int] = Field(
        default=None,
        ge=0,
        le=50,
        description="Actualizar años de experiencia total"
    )
    habilidades: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Actualizar lista de habilidades"
    )
    intereses: Optional[List[str]] = Field(
        default=None,
        max_length=15,
        description="Actualizar áreas de interés"
    )
    linkedin_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Actualizar URL de LinkedIn"
    )
    sitio_web_personal: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Actualizar sitio web personal"
    )
    direccion_residencia: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Actualizar dirección de residencia"
    )
    preferencia_contacto: Optional[PreferenciaContactoEnum] = Field(
        default=None,
        description="Actualizar método de contacto preferido"
    )
    recibir_notificaciones: Optional[bool] = Field(
        default=None,
        description="Actualizar preferencia de notificaciones"
    )
    idiomas: Optional[Dict[str, str]] = Field(
        default=None,
        description="Actualizar idiomas y niveles"
    )
    estado: Optional[EstadoEmprendedorEnum] = Field(
        default=None,
        description="Actualizar estado del emprendedor"
    )
    disponibilidad_tiempo: Optional[str] = Field(
        default=None,
        description="Actualizar disponibilidad de tiempo"
    )
    nivel_educacion: Optional[str] = Field(
        default=None,
        description="Actualizar nivel de educación"
    )
    redes_sociales: Optional[Dict[str, str]] = Field(
        default=None,
        description="Actualizar redes sociales"
    )
    pais_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Actualizar país de residencia"
    )
    ciudad_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Actualizar ciudad de residencia"
    )
    barrio_residencia_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Actualizar barrio de residencia"
    )

class EmprendedorInDB(EmprendedorBase):
    id: int = Field(..., description="ID único del emprendedor")
    usuario_id: int = Field(..., description="ID del usuario asociado")
    pais_residencia_id: Optional[int] = Field(None, description="ID del país de residencia")
    ciudad_residencia_id: Optional[int] = Field(None, description="ID de la ciudad de residencia")
    barrio_residencia_id: Optional[int] = Field(None, description="ID del barrio de residencia")
    fecha_registro: datetime = Field(..., description="Fecha de creación del registro")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última fecha de actualización")
    fecha_verificacion: Optional[datetime] = Field(None, description="Fecha de verificación del perfil")
    score_completitud: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Porcentaje de completitud del perfil"
    )

class EmprendedorConUsuario(EmprendedorInDB):
    usuario: 'UsuarioInDB' = Field(..., description="Información del usuario asociado")

class EmprendedorConUbicacion(EmprendedorInDB):
    pais: Optional['PaisInDB'] = Field(None, description="Información del país de residencia")
    ciudad: Optional['CiudadInDB'] = Field(None, description="Información de la ciudad de residencia")
    barrio: Optional['BarrioInDB'] = Field(None, description="Información del barrio de residencia")

class EmprendedorConNegocios(EmprendedorInDB):
    negocios: List['NegocioInDB'] = Field(default_factory=list, description="Lista de negocios del emprendedor")
    total_negocios: int = Field(0, description="Número total de negocios")
    negocios_activos: int = Field(0, description="Número de negocios activos")
    empleados_totales: int = Field(0, description="Total de empleados en todos los negocios")
    ingresos_totales_anuales: float = Field(0.0, description="Suma de ingresos anuales de todos los negocios")
    promedio_antiguedad_negocios: float = Field(0.0, description="Antigüedad promedio de los negocios en meses")

class EmprendedorCompleto(EmprendedorConUsuario, EmprendedorConUbicacion, EmprendedorConNegocios):
    """Schema completo con toda la información del emprendedor"""
    pass

class EstadisticasEmprendedor(ModeloBase):
    emprendedor_id: int = Field(..., description="ID del emprendedor")
    total_negocios: int = Field(0, description="Total de negocios registrados")
    negocios_activos: int = Field(0, description="Negocios actualmente activos")
    total_empleados: int = Field(0, description="Empleados totales en todos los negocios")
    ingresos_totales: float = Field(0.0, description="Ingresos anuales totales")
    experiencia_total: int = Field(0, description="Años de experiencia total")
    evaluaciones_realizadas: int = Field(0, description="Número de evaluaciones de riesgo realizadas")
    oportunidades_aplicadas: int = Field(0, description="Oportunidades a las que ha aplicado")
    oportunidades_ganadas: int = Field(0, description="Oportunidades obtenidas exitosamente")
    tasa_exito_oportunidades: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Porcentaje de éxito en aplicaciones a oportunidades"
    )
    score_riesgo_promedio: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Puntaje de riesgo promedio en evaluaciones"
    )
    categoria_riesgo_actual: Optional[str] = Field(None, description="Categoría de riesgo más reciente")
    ultima_evaluacion: Optional[datetime] = Field(None, description="Fecha de la última evaluación")

    @model_validator(mode='after')
    def calcular_tasa_exito(self) -> 'EstadisticasEmprendedor':
        if self.oportunidades_aplicadas > 0:
            self.tasa_exito_oportunidades = (self.oportunidades_ganadas / self.oportunidades_aplicadas) * 100
        return self

class PerfilCompletitud(ModeloBase):
    emprendedor_id: int = Field(..., description="ID del emprendedor")
    porcentaje_completitud: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de completitud del perfil")
    campos_completados: List[str] = Field(..., description="Lista de campos completados")
    campos_pendientes: List[str] = Field(..., description="Lista de campos requeridos pendientes")
    nivel_completitud: str = Field(..., description="Nivel: BASICO, INTERMEDIO, AVANZADO, COMPLETO")
    recomendaciones: List[str] = Field(..., description="Recomendaciones para mejorar el perfil")

class FiltroEmprendedores(ModeloBase):
    estado: Optional[EstadoEmprendedorEnum] = Field(
        default=None,
        description="Filtrar por estado del emprendedor"
    )
    ciudad_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filtrar por ciudad de residencia"
    )
    departamento_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filtrar por departamento de residencia"
    )
    pais_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Filtrar por país de residencia"
    )
    sector: Optional[str] = Field(
        default=None,
        description="Filtrar por sector de negocio principal"
    )
    experiencia_minima: Optional[int] = Field(
        default=None,
        ge=0,
        description="Experiencia mínima en años"
    )
    experiencia_maxima: Optional[int] = Field(
        default=None,
        ge=0,
        description="Experiencia máxima en años"
    )
    habilidades: Optional[List[str]] = Field(
        default=None,
        description="Filtrar por habilidades específicas"
    )
    ingresos_minimos: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Ingresos anuales mínimos"
    )
    ingresos_maximos: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Ingresos anuales máximos"
    )
    categoria_riesgo: Optional[str] = Field(
        default=None,
        description="Filtrar por categoría de riesgo actual"
    )
    nivel_completitud: Optional[str] = Field(
        default=None,
        description="Filtrar por nivel de completitud del perfil"
    )
    fecha_registro_desde: Optional[datetime] = Field(
        default=None,
        description="Fecha de registro desde"
    )
    fecha_registro_hasta: Optional[datetime] = Field(
        default=None,
        description="Fecha de registro hasta"
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Número de registros a omitir (paginación)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Límite de registros por página"
    )
    ordenar_por: Optional[str] = Field(
        default="fecha_registro",
        description="Campo para ordenar los resultados"
    )
    orden_descendente: bool = Field(
        default=True,
        description="Ordenar en forma descendente"
    )

class ResumenBusquedaEmprendedores(ModeloBase):
    total_encontrados: int = Field(..., description="Total de emprendedores que coinciden con los filtros")
    total_paginas: int = Field(..., description="Total de páginas según el límite")
    pagina_actual: int = Field(..., description="Página actual")
    por_pagina: int = Field(..., description="Número de resultados por página")
    distribucion_estados: Dict[str, int] = Field(..., description="Distribución por estados")
    distribucion_ciudades: Dict[str, int] = Field(..., description="Distribución por ciudades")
    distribucion_sectores: Dict[str, int] = Field(..., description="Distribución por sectores principales")

class EmprendedorParaRecomendacion(ModeloBase):
    emprendedor: EmprendedorCompleto = Field(..., description="Información completa del emprendedor")
    score_similitud: float = Field(..., ge=0.0, le=100.0, description="Score de similitud para recomendación")
    caracteristicas_compatibles: List[str] = Field(..., description="Características que coinciden con la oportunidad")
    oportunidades_recomendadas: List['OportunidadInDB'] = Field(..., description="Oportunidades recomendadas")

# Importaciones circulares al final para evitar problemas
from schemas.usuarios import UsuarioInDB
from schemas.sistema import PaisInDB, CiudadInDB, BarrioInDB
from schemas.negocios import NegocioInDB
from schemas.oportunidades import OportunidadInDB

# Actualizar referencias en los modelos que las usan
EmprendedorConUsuario.model_rebuild()
EmprendedorConUbicacion.model_rebuild()
EmprendedorConNegocios.model_rebuild()
EmprendedorCompleto.model_rebuild()
EmprendedorParaRecomendacion.model_rebuild()