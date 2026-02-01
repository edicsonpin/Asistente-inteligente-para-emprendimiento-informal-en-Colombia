# schemas/xai.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import ModeloBase

class DificultadImplementacionEnum(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"

class ContextoUsoEnum(str, Enum):
    TOMA_DECISIONES = "TOMA_DECISIONES"
    AUDITORIA = "AUDITORIA"
    CAPACITACION = "CAPACITACION"
    DESARROLLO = "DESARROLLO"

class EmbeddingsCaracteristicasBase(ModeloBase):
    embedding_categoricas: Optional[Dict[str, Any]] = Field(None, description="Embeddings de variables categóricas")
    embedding_final: Optional[Dict[str, Any]] = Field(None, description="Embedding concatenado final")
    modelo_embedding: Optional[str] = Field(None, max_length=100, description="Modelo usado para embeddings")
    dimension_embedding: Optional[int] = Field(None, ge=1, description="Dimensión del embedding")

class EmbeddingsCaracteristicasCreate(EmbeddingsCaracteristicasBase):
    evaluacion_riesgo_id: int = Field(..., gt=0, description="ID de la evaluación asociada")

class EmbeddingsCaracteristicasInDB(EmbeddingsCaracteristicasBase):
    id: int = Field(..., description="ID único del embedding")
    evaluacion_riesgo_id: int = Field(..., description="ID de la evaluación")
    fecha_generacion: datetime = Field(..., description="Fecha de generación")

class ExplicacionContrafactualBase(ModeloBase):
    caracteristicas_originales: Dict[str, Any] = Field(..., description="Características originales")
    caracteristicas_modificadas: Dict[str, Any] = Field(..., description="Características modificadas")
    cambios_sugeridos: List[Dict[str, Any]] = Field(..., description="Cambios específicos sugeridos")
    categoria_original: str = Field(..., description="Categoría de riesgo original")
    categoria_contrafactual: str = Field(..., description="Categoría de riesgo contrafactual")
    puntaje_original: float = Field(..., description="Puntaje original")
    puntaje_contrafactual: float = Field(..., description="Puntaje contrafactual")
    mejora_puntaje: float = Field(..., description="Mejora en puntaje")
    acciones_recomendadas: List[str] = Field(..., description="Acciones recomendadas")
    impacto_acciones: Optional[Dict[str, Any]] = Field(None, description="Impacto esperado por acción")
    dificultad_implementacion: DificultadImplementacionEnum = Field(..., description="Dificultad de implementación")
    algoritmo_contrafactual: Optional[str] = Field(None, max_length=100, description="Algoritmo usado")

class ExplicacionContrafactualCreate(ExplicacionContrafactualBase):
    evaluacion_riesgo_id: int = Field(..., gt=0, description="ID de la evaluación asociada")

class ExplicacionContrafactualInDB(ExplicacionContrafactualBase):
    id: int = Field(..., description="ID único de la explicación")
    evaluacion_riesgo_id: int = Field(..., description="ID de la evaluación")
    fecha_generacion: datetime = Field(..., description="Fecha de generación")

class MetricasEquidadBase(ModeloBase):
    variable_protegida: str = Field(..., max_length=100, description="Variable protegida analizada")
    grupos_analizados: List[str] = Field(..., description="Grupos analizados")
    disparate_impact: float = Field(..., ge=0.0, le=2.0, description="Impacto dispar (4/5 rule)")
    igualdad_oportunidades: float = Field(..., ge=0.0, le=1.0, description="Igualdad de oportunidades")
    igualdad_trato: float = Field(..., ge=0.0, le=1.0, description="Igualdad de trato")
    paridad_demografica: float = Field(..., ge=0.0, le=1.0, description="Paridad demográfica")
    metricas_por_grupo: Dict[str, Any] = Field(..., description="Métricas por grupo")
    brechas_deteccion: Optional[Dict[str, Any]] = Field(None, description="Brechas detectadas")
    cumple_umbral_equidad: bool = Field(..., description="Cumple umbral de equidad")
    umbral_equidad: float = Field(0.8, ge=0.0, le=1.0, description="Umbral de equidad")
    recomendaciones_mitigacion: Optional[List[str]] = Field(None, description="Recomendaciones de mitigación")

class MetricasEquidadCreate(MetricasEquidadBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo evaluado")

class MetricasEquidadInDB(MetricasEquidadBase):
    id: int = Field(..., description="ID único de las métricas")
    modelo_ia_id: int = Field(..., description="ID del modelo")
    fecha_evaluacion: datetime = Field(..., description="Fecha de evaluación")

class AuditoriaExplicabilidadBase(ModeloBase):
    claridad_explicacion: int = Field(..., ge=1, le=5, description="Claridad de la explicación (1-5)")
    utilidad_explicacion: int = Field(..., ge=1, le=5, description="Utilidad de la explicación (1-5)")
    confianza_explicacion: int = Field(..., ge=1, le=5, description="Confianza en la explicación (1-5)")
    accionabilidad_explicacion: int = Field(..., ge=1, le=5, description="Accionabilidad (1-5)")
    comentarios: Optional[str] = Field(None, description="Comentarios del usuario")
    sugerencias_mejora: Optional[str] = Field(None, description="Sugerencias de mejora")
    entendio_recomendaciones: bool = Field(..., description="Entendió las recomendaciones")
    contexto_uso: ContextoUsoEnum = Field(..., description="Contexto de uso de la explicación")

class AuditoriaExplicabilidadCreate(AuditoriaExplicabilidadBase):
    evaluacion_riesgo_id: int = Field(..., gt=0, description="ID de la evaluación")
    usuario_id: int = Field(..., gt=0, description="ID del usuario que audita")

class AuditoriaExplicabilidadInDB(AuditoriaExplicabilidadBase):
    id: int = Field(..., description="ID único de la auditoría")
    evaluacion_riesgo_id: int = Field(..., description="ID de la evaluación")
    usuario_id: int = Field(..., description="ID del usuario")
    fecha_auditoria: datetime = Field(..., description="Fecha de auditoría")

class SHAPAnalysisBase(ModeloBase):
    importancia_global: Dict[str, float] = Field(..., description="Importancia global de características")
    dependencias_caracteristicas: Optional[Dict[str, Any]] = Field(None, description="Dependencias entre características")
    interacciones_caracteristicas: Optional[Dict[str, Any]] = Field(None, description="Interacciones entre características")
    valores_shap_base: Optional[Dict[str, Any]] = Field(None, description="Valores base SHAP")
    expected_value: Optional[float] = Field(None, description="Valor esperado SHAP")
    consistencia_explicaciones: Optional[float] = Field(None, ge=0.0, le=1.0, description="Consistencia entre explicaciones")
    estabilidad_shap: Optional[float] = Field(None, ge=0.0, le=1.0, description="Estabilidad de valores SHAP")
    tamaño_muestra: Optional[int] = Field(None, ge=1, description="Tamaño de muestra usado")

class SHAPAnalysisCreate(SHAPAnalysisBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo analizado")

class SHAPAnalysisInDB(SHAPAnalysisBase):
    id: int = Field(..., description="ID único del análisis")
    modelo_ia_id: int = Field(..., description="ID del modelo")
    fecha_analisis: datetime = Field(..., description="Fecha del análisis")

class AnalisisEquidad(ModeloBase):
    modelo_id: int = Field(..., description="ID del modelo")
    variable_protegida: str = Field(..., description="Variable protegida")
    metricas: MetricasEquidadInDB = Field(..., description="Métricas de equidad")
    recomendaciones: List[str] = Field(..., description="Recomendaciones")
    estado_cumplimiento: str = Field(..., description="CUMPLE, ALERTA, NO_CUMPLE")
    acciones_mitigacion: List[str] = Field(..., description="Acciones de mitigación")

class ResumenExplicabilidad(ModeloBase):
    evaluacion_id: int = Field(..., description="ID de la evaluación")
    explicaciones_shap: Optional[Dict[str, Any]] = Field(None, description="Explicaciones SHAP")
    explicaciones_lime: Optional[Dict[str, Any]] = Field(None, description="Explicaciones LIME")
    contrafactual: Optional[ExplicacionContrafactualInDB] = Field(None, description="Explicación contrafactual")
    auditorias: List[AuditoriaExplicabilidadInDB] = Field(default_factory=list, description="Auditorías realizadas")
    calificacion_promedio: float = Field(0.0, ge=0.0, le=5.0, description="Calificación promedio")
    nivel_confianza: str = Field(..., description="ALTO, MEDIO, BAJO")