# schemas/mlops.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import ModeloBase

class EstadoPipelineEnum(str, Enum):
    INACTIVO = "INACTIVO"
    ACTIVO = "ACTIVO"
    PAUSADO = "PAUSADO"
    ERROR = "ERROR"

class EstadoEjecucionEnum(str, Enum):
    EN_EJECUCION = "EN_EJECUCION"
    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"
    CANCELADO = "CANCELADO"

class VersionModeloMLflowBase(ModeloBase):
    run_id: str = Field(..., min_length=1, max_length=100, description="ID único del run en MLflow")
    experiment_id: str = Field(..., min_length=1, max_length=100, description="ID del experimento")
    artifact_uri: Optional[str] = Field(None, max_length=500, description="URI de los artifacts")
    parametros_entrenamiento: Optional[Dict[str, Any]] = Field(None, description="Parámetros de entrenamiento")
    metricas_evaluacion: Optional[Dict[str, Any]] = Field(None, description="Métricas de evaluación")
    tags_mlflow: Optional[Dict[str, Any]] = Field(None, description="Tags en MLflow")
    usuario_registro: Optional[str] = Field(None, max_length=100, description="Usuario que registró")

class VersionModeloMLflowCreate(VersionModeloMLflowBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo asociado")
    fecha_registro: datetime = Field(..., description="Fecha de registro en MLflow")

class VersionModeloMLflowInDB(VersionModeloMLflowBase):
    id: int = Field(..., description="ID único del registro")
    modelo_ia_id: int = Field(..., description="ID del modelo")
    fecha_registro: datetime = Field(..., description="Fecha de registro")

class PipelineMLOpsBase(ModeloBase):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre único del pipeline")
    descripcion: Optional[str] = Field(None, description="Descripción del pipeline")
    etapas: List[str] = Field(..., description="Etapas del pipeline")
    configuracion: Optional[Dict[str, Any]] = Field(None, description="Configuración del pipeline")
    estado: EstadoPipelineEnum = Field(EstadoPipelineEnum.INACTIVO, description="Estado actual")
    activo: bool = Field(True, description="Pipeline activo")

class PipelineMLOpsCreate(PipelineMLOpsBase):
    pass

class PipelineMLOpsInDB(PipelineMLOpsBase):
    id: int = Field(..., description="ID único del pipeline")
    fecha_creacion: datetime = Field(..., description="Fecha de creación")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Última actualización")
    ultima_ejecucion: Optional[datetime] = Field(None, description="Última ejecución")
    proxima_ejecucion: Optional[datetime] = Field(None, description="Próxima ejecución programada")
    exitos: int = Field(0, description="Número de ejecuciones exitosas")
    fallos: int = Field(0, description="Número de ejecuciones fallidas")
    tiempo_promedio: Optional[float] = Field(None, description="Tiempo promedio de ejecución")

class EjecucionPipelineBase(ModeloBase):
    estado: EstadoEjecucionEnum = Field(..., description="Estado de la ejecución")
    metricas_salida: Optional[Dict[str, Any]] = Field(None, description="Métricas de salida")
    logs_ejecucion: Optional[str] = Field(None, description="Logs de ejecución")
    errores: Optional[str] = Field(None, description="Errores encontrados")
    consumo_cpu: Optional[float] = Field(None, ge=0.0, description="Consumo de CPU")
    consumo_memoria: Optional[float] = Field(None, ge=0.0, description="Consumo de memoria en MB")
    consumo_gpu: Optional[float] = Field(None, ge=0.0, description="Consumo de GPU")

class EjecucionPipelineCreate(EjecucionPipelineBase):
    pipeline_id: int = Field(..., gt=0, description="ID del pipeline")
    modelo_ia_id: Optional[int] = Field(None, gt=0, description="ID del modelo generado")

class EjecucionPipelineInDB(EjecucionPipelineBase):
    id: int = Field(..., description="ID único de la ejecución")
    pipeline_id: int = Field(..., description="ID del pipeline")
    modelo_ia_id: Optional[int] = Field(None, description="ID del modelo")
    fecha_inicio: datetime = Field(..., description="Fecha de inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha de fin")
    duracion_segundos: Optional[float] = Field(None, description="Duración en segundos")

class MonitoreoModeloBase(ModeloBase):
    accuracy_produccion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy en producción")
    precision_produccion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Precisión en producción")
    recall_produccion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall en producción")
    f1_score_produccion: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1-Score en producción")
    drift_datos: Optional[float] = Field(None, ge=0.0, le=1.0, description="Drift de datos detectado")
    drift_concepto: Optional[float] = Field(None, ge=0.0, le=1.0, description="Drift de concepto detectado")
    score_degradacion: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de degradación")
    solicitudes_totales: int = Field(0, description="Total de solicitudes")
    solicitudes_exitosas: int = Field(0, description="Solicitudes exitosas")
    tasa_error: Optional[float] = Field(None, ge=0.0, le=1.0, description="Tasa de error")
    latencia_promedio: Optional[float] = Field(None, ge=0.0, description="Latencia promedio en ms")
    periodo_muestreo: str = Field("HOURLY", description="HOURLY, DAILY, WEEKLY")

class MonitoreoModeloCreate(MonitoreoModeloBase):
    modelo_ia_id: int = Field(..., gt=0, description="ID del modelo monitoreado")

class MonitoreoModeloInDB(MonitoreoModeloBase):
    id: int = Field(..., description="ID único del monitoreo")
    modelo_ia_id: int = Field(..., description="ID del modelo")
    fecha_monitoreo: datetime = Field(..., description="Fecha del monitoreo")

class MetricasDrift(ModeloBase):
    drift_datos: float = Field(..., ge=0.0, le=1.0, description="Nivel de drift de datos")
    drift_concepto: float = Field(..., ge=0.0, le=1.0, description="Nivel de drift de concepto")
    caracteristicas_afectadas: List[str] = Field(..., description="Características con mayor drift")
    fecha_deteccion: datetime = Field(..., description="Fecha de detección")
    recomendaciones: List[str] = Field(..., description="Recomendaciones de acción")
    umbral_alerta: float = Field(0.1, description="Umbral que activa alertas")

class EstadoPipeline(ModeloBase):
    pipeline_id: int = Field(..., description="ID del pipeline")
    nombre: str = Field(..., description="Nombre del pipeline")
    estado: EstadoPipelineEnum = Field(..., description="Estado actual")
    ultima_ejecucion: Optional[datetime] = Field(None, description="Última ejecución")
    proxima_ejecucion: Optional[datetime] = Field(None, description="Próxima ejecución")
    exitos: int = Field(..., description="Ejecuciones exitosas")
    fallos: int = Field(..., description="Ejecuciones fallidas")
    tiempo_promedio: Optional[float] = Field(None, description="Tiempo promedio")
    salud: str = Field(..., description="SALUDABLE, ADVERTENCIA, CRITICO")