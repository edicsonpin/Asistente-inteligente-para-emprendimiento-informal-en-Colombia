# schemas/sinteticos.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import ModeloBase

class TipoGeneradorEnum(str, Enum):
    CTGAN = "CTGAN"
    VAE = "VAE"
    GAN = "GAN"
    COPULA = "COPULA"
    SMOTE = "SMOTE"

class TipoDatoSinteticoEnum(str, Enum):
    ENTRENAMIENTO = "ENTRENAMIENTO"
    VALIDACION = "VALIDACION"
    BALANCEO = "BALANCEO"
    PRUEBA = "PRUEBA"

class EstrategiaBalanceoEnum(str, Enum):
    OVERSAMPLING = "OVERSAMPLING"
    UNDERSAMPLING = "UNDERSAMPLING"
    SMOTE = "SMOTE"
    ADASYN = "ADASYN"
    COMBINADO = "COMBINADO"

class DatosSinteticosBase(ModeloBase):
    modelo_generador: str = Field(..., max_length=100, description="Modelo generador usado")
    version_modelo: str = Field(..., max_length=20, description="Versión del modelo generador")
    tipo_dato: TipoDatoSinteticoEnum = Field(..., description="Tipo de dato sintético generado")
    caracteristicas_generadas: Dict[str, Any] = Field(..., description="Características generadas")
    tamaño_dataset: int = Field(..., ge=1, description="Tamaño del dataset generado")
    parametros_generacion: Optional[Dict[str, Any]] = Field(None, description="Parámetros de generación")
    score_calidad: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de calidad")
    metricas_similitud: Optional[Dict[str, Any]] = Field(None, description="Métricas de similitud")
    utilizado_entrenamiento: bool = Field(False, description="Ya utilizado para entrenamiento")

class DatosSinteticosCreate(DatosSinteticosBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo generador")
    modelo_destino_id: Optional[int] = Field(None, gt=0, description="ID del modelo destino")

class DatosSinteticosInDB(DatosSinteticosBase):
    id: int = Field(..., description="ID único de los datos")
    modelo_ia_id: int = Field(..., description="ID del modelo generador")
    modelo_destino_id: Optional[int] = Field(None, description="ID del modelo destino")
    fecha_generacion: datetime = Field(..., description="Fecha de generación")

class GeneradorSinteticoBase(ModeloBase):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del generador")
    tipo: TipoGeneradorEnum = Field(..., description="Tipo de generador")
    descripcion: Optional[str] = Field(None, description="Descripción del generador")
    hiperparametros: Optional[Dict[str, Any]] = Field(None, description="Hiperparámetros configurables")
    arquitectura: Optional[Dict[str, Any]] = Field(None, description="Arquitectura del generador")
    caracteristicas_soportadas: List[str] = Field(..., description="Características que puede generar")
    accuracy_generacion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy de generación")
    diversidad_generada: Optional[float] = Field(None, ge=0.0, le=1.0, description="Diversidad de datos generados")
    fidelidad_datos: Optional[float] = Field(None, ge=0.0, le=1.0, description="Fidelidad a datos reales")
    limite_generacion_diaria: int = Field(1000, ge=1, description="Límite diario de generación")
    activo: bool = Field(True, description="Generador activo")

class GeneradorSinteticoCreate(GeneradorSinteticoBase):
    pass

class GeneradorSinteticoInDB(GeneradorSinteticoBase):
    id: int = Field(..., description="ID único del generador")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última actualización")
    datos_generados_totales: int = Field(0, description="Total de datos generados")
    ultima_generacion: Optional[datetime] = Field(None, description="Última generación")
    estado: str = Field("INACTIVO", description="Estado actual del generador")

class CalidadDatosSinteticosBase(ModeloBase):
    correlacion_promedio: Optional[float] = Field(None, ge=0.0, le=1.0, description="Correlación promedio con datos reales")
    distancia_distribucion: Optional[float] = Field(None, ge=0.0, description="Distancia entre distribuciones")
    preservacion_varianza: Optional[float] = Field(None, ge=0.0, le=1.0, description="Preservación de varianza")
    score_utilidad: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de utilidad para entrenamiento")
    preservacion_relaciones: Optional[float] = Field(None, ge=0.0, le=1.0, description="Preservación de relaciones")
    capacidad_generalizacion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Capacidad de generalización")
    riesgo_reenidentificacion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Riesgo de re-identificación")
    distancia_records_reales: Optional[float] = Field(None, ge=0.0, description="Distancia a records reales")
    score_privacidad: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de privacidad")
    score_calidad_total: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score total de calidad")
    cumple_umbral_calidad: bool = Field(..., description="Cumple umbral mínimo de calidad")
    recomendaciones_mejora: Optional[List[str]] = Field(None, description="Recomendaciones para mejorar calidad")

class CalidadDatosSinteticosCreate(CalidadDatosSinteticosBase):
    datos_sinteticos_id: int = Field(..., gt=0, description="ID de los datos evaluados")

class CalidadDatosSinteticosInDB(CalidadDatosSinteticosBase):
    id: int = Field(..., description="ID único de la evaluación")
    datos_sinteticos_id: int = Field(..., description="ID de los datos")
    fecha_evaluacion: datetime = Field(..., description="Fecha de evaluación")

class BalanceoSesgoBase(ModeloBase):
    variable_balanceo: str = Field(..., max_length=100, description="Variable a balancear")
    distribucion_original: Dict[str, float] = Field(..., description="Distribución original")
    distribucion_objetivo: Dict[str, float] = Field(..., description="Distribución objetivo")
    distribucion_lograda: Dict[str, float] = Field(..., description="Distribución lograda")
    mejora_balanceo: float = Field(..., ge=0.0, description="Mejora en balanceo")
    reduccion_sesgo: float = Field(..., ge=0.0, le=1.0, description="Reducción de sesgo")
    impacto_rendimiento: Optional[float] = Field(None, description="Impacto en rendimiento del modelo")
    estrategia_balanceo: EstrategiaBalanceoEnum = Field(..., description="Estrategia de balanceo aplicada")
    parametros_estrategia: Optional[Dict[str, Any]] = Field(None, description="Parámetros de la estrategia")
    metricas_antes: Dict[str, Any] = Field(..., description="Métricas antes del balanceo")
    metricas_despues: Dict[str, Any] = Field(..., description="Métricas después del balanceo")
    mejora_equidad: float = Field(..., ge=0.0, le=1.0, description="Mejora en equidad")

class BalanceoSesgoCreate(BalanceoSesgoBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo balanceado")
    datos_sinteticos_id: int = Field(..., gt=0, description="ID de datos sintéticos usados")

class BalanceoSesgoInDB(BalanceoSesgoBase):
    id: int = Field(..., description="ID único del balanceo")
    modelo_ia_id: int = Field(..., description="ID del modelo")
    datos_sinteticos_id: int = Field(..., description="ID de los datos")
    fecha_balanceo: datetime = Field(..., description="Fecha del balanceo")

class SolicitudGeneracionSintetica(ModeloBase):
    generador_id: int = Field(..., gt=0, description="ID del generador a usar")
    tamaño: int = Field(1000, ge=1, le=100000, description="Tamaño del dataset a generar")
    caracteristicas: List[str] = Field(..., description="Características a incluir")
    parametros_personalizados: Optional[Dict[str, Any]] = Field(None, description="Parámetros personalizados")
    proposito: TipoDatoSinteticoEnum = Field(..., description="Propósito de la generación")
    balancear_variable: Optional[str] = Field(None, description="Variable a balancear")

class ResultadoGeneracionSintetica(ModeloBase):
    solicitud: SolicitudGeneracionSintetica = Field(..., description="Solicitud original")
    datos_generados: DatosSinteticosInDB = Field(..., description="Datos generados")
    calidad: Optional[CalidadDatosSinteticosInDB] = Field(None, description="Evaluación de calidad")
    tiempo_generacion: float = Field(..., description="Tiempo de generación en segundos")
    estado: str = Field(..., description="EXITOSO, FALLIDO, PARCIAL")
    mensaje: Optional[str] = Field(None, description="Mensaje adicional")