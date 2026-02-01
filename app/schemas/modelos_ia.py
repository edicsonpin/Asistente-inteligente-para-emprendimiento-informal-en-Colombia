# schemas/modelos_ia.py

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator 
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import ModeloBase

class TipoModeloEnum(str, Enum):
    ENSEMBLE = "ENSEMBLE"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    LINEAR = "LINEAR"
    VOTING = "VOTING"
    NEURAL_NETWORK = "NEURAL_NETWORK"
    HYBRID_LIGHTGBM_NN = "HYBRID_LIGHTGBM_NN"

class EstadoModeloEnum(str, Enum):
    EN_ENTRENAMIENTO = "EN_ENTRENAMIENTO"
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    DEPRECADO = "DEPRECADO"
    ERROR = "ERROR"

class ModeloIABase(ModeloBase):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre único del modelo")
    tipo: TipoModeloEnum = Field(..., description="Tipo de arquitectura del modelo")
    version: str = Field("1.0.0", pattern=r'^\d+\.\d+\.\d+$', description="Versión semántica")
    arquitectura: Optional[str] = Field(None, max_length=100, description="Arquitectura específica")
    componentes: Optional[Dict[str, Any]] = Field(None, description="Componentes del modelo híbrido")
    accuracy: float = Field(0.0, ge=0.0, le=1.0, description="Precisión general del modelo")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="Precisión por clase")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall del modelo")
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1-Score")
    mejora_precision: Optional[float] = Field(None, description="Mejora respecto a línea base")
    comparacion_linea_base: Optional[Dict[str, Any]] = Field(None, description="Comparación con baseline")
    parametros: Optional[Dict[str, Any]] = Field(None, description="Hiperparámetros del modelo")
    ruta_modelo: Optional[str] = Field(None, max_length=500, description="Ruta al archivo del modelo")
    descripcion: Optional[str] = Field(None, description="Descripción del modelo")
    activo: bool = Field(True, description="Modelo activo en el sistema")
    es_produccion: bool = Field(False, description="Modelo en producción")
    mlflow_registered: bool = Field(False, description="Registrado en MLflow")
    mlflow_version: Optional[str] = Field(None, description="Versión en MLflow")
    estado: EstadoModeloEnum = Field(EstadoModeloEnum.EN_ENTRENAMIENTO, description="Estado actual")

    @field_validator('nombre')
    @classmethod
    def validar_nombre_unico(cls, v: str) -> str:
        # En una implementación real, verificaríamos contra la base de datos
        if len(v.strip()) < 3:
            raise ValueError('El nombre del modelo debe tener al menos 3 caracteres')
        return v.strip()

    @model_validator(mode='after')
    def validar_metricas(self) -> 'ModeloIABase':
        if self.precision and self.recall and self.f1_score:
            # Validar coherencia entre métricas
            f1_calculado = 2 * (self.precision * self.recall) / (self.precision + self.recall) if (self.precision + self.recall) > 0 else 0
            if abs(f1_calculado - self.f1_score) > 0.1:
                raise ValueError('Las métricas F1, precisión y recall no son coherentes')
        return self

class ModeloIACreate(ModeloIABase):
    pass

class ModeloIAUpdate(ModeloBase):
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    precision: Optional[float] = Field(None, ge=0.0, le=1.0)
    recall: Optional[float] = Field(None, ge=0.0, le=1.0)
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    mejora_precision: Optional[float] = None
    comparacion_linea_base: Optional[Dict[str, Any]] = None
    parametros: Optional[Dict[str, Any]] = None
    ruta_modelo: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    es_produccion: Optional[bool] = None
    mlflow_registered: Optional[bool] = None
    mlflow_version: Optional[str] = None
    estado: Optional[EstadoModeloEnum] = None

class ModeloIAInDB(ModeloIABase):
    id: int = Field(..., description="ID único del modelo")
    fecha_entrenamiento: datetime = Field(..., description="Fecha de entrenamiento")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última actualización")

class ModeloIAConMetricas(ModeloIAInDB):
    total_evaluaciones: int = Field(0, description="Total de evaluaciones realizadas")
    distribucion_riesgo: Dict[str, int] = Field(..., description="Distribución de categorías")
    confianza_promedio: float = Field(0.0, ge=0.0, le=1.0, description="Confianza promedio")
    tiempo_inferencia_promedio: float = Field(0.0, description="Tiempo de inferencia promedio")
    uso_ultimo_mes: int = Field(0, description="Usos en el último mes")

class MetricasModelo(ModeloBase):
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    auc_roc: Optional[float] = Field(None, ge=0.0, le=1.0)
    log_loss: Optional[float] = Field(None, ge=0.0)
    matriz_confusion: Optional[Dict[str, Any]] = Field(None, description="Matriz de confusión")
    reporte_clasificacion: Optional[Dict[str, Any]] = Field(None, description="Reporte de clasificación")

class EntrenamientoModelo(ModeloBase):
    modelo_id: int = Field(..., gt=0, description="ID del modelo")
    dataset_entrenamiento: str = Field(..., description="Ruta del dataset de entrenamiento")
    parametros_entrenamiento: Dict[str, Any] = Field(..., description="Parámetros de entrenamiento")
    caracteristicas_utilizadas: List[str] = Field(..., description="Características utilizadas")
    tamaño_dataset: int = Field(..., gt=0, description="Tamaño del dataset")
    tiempo_entrenamiento: float = Field(..., gt=0.0, description="Tiempo de entrenamiento en segundos")
    metricas_entrenamiento: MetricasModelo = Field(..., description="Métricas de entrenamiento")
    metricas_validacion: Optional[MetricasModelo] = Field(None, description="Métricas de validación")

class EvolucionMetricas(ModeloBase):
    fecha: datetime = Field(..., description="Fecha del entrenamiento")
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    tamaño_dataset: int = Field(..., gt=0)
    version_modelo: str = Field(..., description="Versión del modelo")

class FiltroModelosIA(ModeloBase):
    tipo: Optional[TipoModeloEnum] = Field(None, description="Filtrar por tipo")
    activo: Optional[bool] = Field(None, description="Filtrar por estado activo")
    es_produccion: Optional[bool] = Field(None, description="Filtrar por modelos en producción")
    accuracy_minimo: Optional[float] = Field(None, ge=0.0, le=1.0, description="Precisión mínima")
    estado: Optional[EstadoModeloEnum] = Field(None, description="Filtrar por estado")
    skip: int = Field(0, ge=0, description="Registros a omitir")
    limit: int = Field(100, ge=1, le=1000, description="Límite de registros")