# schemas/evaluaciones.py
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from .base import ModeloBase

class CategoriaRiesgoEnum(str, Enum):
    MUY_BAJO = "MUY_BAJO"
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"

class EvaluacionRiesgoBase(ModeloBase):
    probabilidad_muy_bajo: float = Field(0.0, ge=0.0, le=1.0, description="Probabilidad categoría MUY_BAJO")
    probabilidad_bajo: float = Field(0.0, ge=0.0, le=1.0, description="Probabilidad categoría BAJO")
    probabilidad_medio: float = Field(0.0, ge=0.0, le=1.0, description="Probabilidad categoría MEDIO")
    probabilidad_alto: float = Field(0.0, ge=0.0, le=1.0, description="Probabilidad categoría ALTO")
    probabilidad_muy_alto: float = Field(0.0, ge=0.0, le=1.0, description="Probabilidad categoría MUY_ALTO")
    categoria_riesgo: CategoriaRiesgoEnum = Field(..., description="Categoría de riesgo asignada")
    puntaje_riesgo: int = Field(..., ge=0, le=1000, description="Puntaje de riesgo (0-1000)")
    confianza_prediccion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confianza del modelo")
    explicacion_final: Optional[str] = Field(None, description="Explicación en lenguaje natural")
    caracteristicas_importantes: Optional[Dict[str, float]] = Field(None, description="Importancia de características")
    explicacion_contrafactual: Optional[Dict[str, Any]] = Field(None, description="Explicación contrafactual")
    caracteristicas_sugeridas: Optional[Dict[str, Any]] = Field(None, description="Características sugeridas para mejora")
    impacto_caracteristicas: Optional[Dict[str, float]] = Field(None, description="Impacto de características en score")
    metricas_equidad: Optional[Dict[str, Any]] = Field(None, description="Métricas de equidad y sesgo")
    variables_protegidas_analizadas: Optional[List[str]] = Field(None, description="Variables protegidas analizadas")
    tiempo_procesamiento: Optional[float] = Field(None, ge=0.0, description="Tiempo de procesamiento en segundos")

    @model_validator(mode='after')
    def validar_probabilidades(self) -> 'EvaluacionRiesgoBase':
        probabilidades = [
            self.probabilidad_muy_bajo,
            self.probabilidad_bajo, 
            self.probabilidad_medio,
            self.probabilidad_alto,
            self.probabilidad_muy_alto
        ]
        
        total = sum(probabilidades)
        if abs(total - 1.0) > 0.01:  # 1% de tolerancia
            raise ValueError(f'La suma de probabilidades debe ser 1.0, actual: {total}')
        
        # Validar que la categoría asignada coincida con la mayor probabilidad
        max_prob = max(probabilidades)
        max_index = probabilidades.index(max_prob)
        categorias_esperadas = list(CategoriaRiesgoEnum)
        
        if categorias_esperadas[max_index] != self.categoria_riesgo:
            raise ValueError('La categoría asignada no coincide con la probabilidad máxima')
        
        return self

    @field_validator('puntaje_riesgo')
    @classmethod
    def validar_puntaje_categoria(cls, v: int, values: Any) -> int:
        if 'categoria_riesgo' in values.data:
            categoria = values.data['categoria_riesgo']
            rangos = {
                'MUY_BAJO': (0, 200),
                'BAJO': (201, 400),
                'MEDIO': (401, 600),
                'ALTO': (601, 800),
                'MUY_ALTO': (801, 1000)
            }
            
            if categoria in rangos:
                min_val, max_val = rangos[categoria]
                if not (min_val <= v <= max_val):
                    raise ValueError(f'Puntaje {v} no corresponde a categoría {categoria}')
        
        return v

class EvaluacionRiesgoCreate(EvaluacionRiesgoBase):
    emprendedor_id: int = Field(..., gt=0, description="ID del emprendedor evaluado")
    negocio_id: int = Field(..., gt=0, description="ID del negocio evaluado")
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo de IA utilizado")
    version_modelo: str = Field(..., min_length=1, description="Versión del modelo utilizado")

class EvaluacionRiesgoUpdate(ModeloBase):
    explicacion_shap: Optional[Dict[str, Any]] = Field(None, description="Explicaciones SHAP")
    explicacion_lime: Optional[Dict[str, Any]] = Field(None, description="Explicaciones LIME")
    explicacion_global: Optional[Dict[str, Any]] = Field(None, description="Explicación global del modelo")
    explicacion_final: Optional[str] = Field(None, description="Explicación final para usuario")
    caracteristicas_importantes: Optional[Dict[str, float]] = Field(None, description="Características importantes")
    explicacion_contrafactual: Optional[Dict[str, Any]] = Field(None, description="Explicación contrafactual")
    caracteristicas_sugeridas: Optional[Dict[str, Any]] = Field(None, description="Características sugeridas")
    impacto_caracteristicas: Optional[Dict[str, float]] = Field(None, description="Impacto de características")
    metricas_equidad: Optional[Dict[str, Any]] = Field(None, description="Métricas de equidad")

class EvaluacionRiesgoInDB(EvaluacionRiesgoBase):
    id: int = Field(..., description="ID único de la evaluación")
    emprendedor_id: int = Field(..., description="ID del emprendedor")
    negocio_id: int = Field(..., description="ID del negocio")
    modelo_ia_id: int = Field(..., description="ID del modelo de IA")
    fecha_evaluacion: datetime = Field(..., description="Fecha de evaluación")
    version_modelo: str = Field(..., description="Versión del modelo")
    explicacion_shap: Optional[Dict[str, Any]] = Field(None, description="Explicaciones SHAP")
    explicacion_lime: Optional[Dict[str, Any]] = Field(None, description="Explicaciones LIME")
    explicacion_global: Optional[Dict[str, Any]] = Field(None, description="Explicación global")

class EvaluacionRiesgoCompleta(EvaluacionRiesgoInDB):
    emprendedor: 'EmprendedorInDB' = Field(..., description="Información del emprendedor")
    negocio: 'NegocioInDB' = Field(..., description="Información del negocio")
    modelo: 'ModeloIAInDB' = Field(..., description="Información del modelo")

class ExplicacionSHAP(ModeloBase):
    valores_base: float = Field(..., description="Valor base SHAP")
    valores_shap: Dict[str, float] = Field(..., description="Valores SHAP por característica")
    importancia_global: Dict[str, float] = Field(..., description="Importancia global de características")
    dependencias: Optional[Dict[str, Any]] = Field(None, description="Gráficos de dependencia")
    force_plot: Optional[Dict[str, Any]] = Field(None, description="Datos para force plot")

class ExplicacionContrafactual(ModeloBase):
    caracteristicas_originales: Dict[str, Any] = Field(..., description="Características originales")
    caracteristicas_modificadas: Dict[str, Any] = Field(..., description="Características modificadas")
    cambios_sugeridos: List[Dict[str, Any]] = Field(..., description="Cambios específicos sugeridos")
    categoria_original: str = Field(..., description="Categoría original")
    categoria_contrafactual: str = Field(..., description="Categoría contrafactual")
    mejora_puntaje: float = Field(..., description="Mejora en puntaje")
    acciones_recomendadas: List[str] = Field(..., description="Acciones recomendadas")
    impacto_esperado: Dict[str, float] = Field(..., description="Impacto esperado por acción")
    dificultad_implementacion: str = Field(..., description="BAJA, MEDIA, ALTA")

class SolicitudEvaluacion(ModeloBase):
    negocio_id: int = Field(..., gt=0, description="ID del negocio a evaluar")
    emprendedor_id: int = Field(..., gt=0, description="ID del emprendedor")
    caracteristicas: Dict[str, Any] = Field(..., description="Características para evaluación")
    incluir_explicaciones: bool = Field(True, description="Incluir explicaciones XAI")
    generar_contrafactual: bool = Field(False, description="Generar explicación contrafactual")
    modelo_preferido: Optional[int] = Field(None, gt=0, description="ID de modelo preferido")

class ResultadoEvaluacion(ModeloBase):
    evaluacion: EvaluacionRiesgoInDB = Field(..., description="Evaluación completa")
    explicaciones: Optional[ExplicacionSHAP] = Field(None, description="Explicaciones SHAP")
    contrafactual: Optional[ExplicacionContrafactual] = Field(None, description="Explicación contrafactual")
    recomendaciones: List[str] = Field(default_factory=list, description="Recomendaciones específicas")
    alertas: List[str] = Field(default_factory=list, description="Alertas importantes")

class EstadisticasEvaluacion(ModeloBase):
    total_evaluaciones: int = Field(0, description="Total de evaluaciones")
    distribucion_riesgo: Dict[str, int] = Field(..., description="Distribución por categoría")
    confianza_promedio: float = Field(0.0, ge=0.0, le=1.0, description="Confianza promedio")
    precision_estimada: float = Field(0.0, ge=0.0, le=1.0, description="Precisión estimada")
    tendencia_ultimo_mes: Dict[str, int] = Field(..., description="Tendencia último mes")
    modelo_mas_utilizado: Optional[str] = Field(None, description="Modelo más utilizado")
    tiempo_promedio_procesamiento: float = Field(0.0, description="Tiempo promedio en segundos")

class FiltroEvaluaciones(ModeloBase):
    emprendedor_id: Optional[int] = Field(None, gt=0, description="Filtrar por emprendedor")
    negocio_id: Optional[int] = Field(None, gt=0, description="Filtrar por negocio")
    modelo_ia_id: Optional[int] = Field(None, gt=0, description="Filtrar por modelo")
    categoria_riesgo: Optional[CategoriaRiesgoEnum] = Field(None, description="Filtrar por categoría")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    confianza_minima: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confianza mínima")
    skip: int = Field(0, ge=0, description="Registros a omitir")
    limit: int = Field(100, ge=1, le=1000, description="Límite de registros")

# Importaciones circulares
from schemas.emprendedores import EmprendedorInDB
from schemas.negocios import NegocioInDB
from schemas.modelos_ia import ModeloIAInDB

# Rebuild models
EvaluacionRiesgoCompleta.model_rebuild()