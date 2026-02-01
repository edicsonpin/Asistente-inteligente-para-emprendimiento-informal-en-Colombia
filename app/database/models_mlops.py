# database/models_mlops.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .models import Base

class VersionModeloMLflow(Base):
    __tablename__ = "versiones_mlflow"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Metadatos de MLflow
    run_id = Column(String(100), unique=True)
    experiment_id = Column(String(100))
    artifact_uri = Column(String(500))
    
    # Información del experimento
    parametros_entrenamiento = Column(JSON)
    metricas_evaluacion = Column(JSON)
    tags_mlflow = Column(JSON)
    
    # Trazabilidad
    fecha_registro = Column(DateTime(timezone=True))
    usuario_registro = Column(String(100))
    
    modelo = relationship("ModeloIA", back_populates="versiones_mlflow")

class PipelineMLOps(Base):
    __tablename__ = "pipelines_mlops"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    
    # Configuración del pipeline
    etapas = Column(JSON)  # ['data_processing', 'training', 'evaluation', 'deployment']
    configuracion = Column(JSON)
    
    # Estado y ejecución
    estado = Column(String(50), default="INACTIVO")
    ultima_ejecucion = Column(DateTime(timezone=True))
    proxima_ejecucion = Column(DateTime(timezone=True))
    
    # Métricas
    exitos = Column(Integer, default=0)
    fallos = Column(Integer, default=0)
    tiempo_promedio = Column(Float)
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    activo = Column(Boolean, default=True)

class EjecucionPipeline(Base):
    __tablename__ = "ejecuciones_pipeline"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines_mlops.id"))
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Información de ejecución
    estado = Column(String(50))  # 'EN_EJECUCION', 'EXITOSO', 'FALLIDO'
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True))
    duracion_segundos = Column(Float)
    
    # Resultados
    metricas_salida = Column(JSON)
    logs_ejecucion = Column(Text)
    errores = Column(Text)
    
    # Recursos
    consumo_cpu = Column(Float)
    consumo_memoria = Column(Float)
    consumo_gpu = Column(Float)
    
    # Relaciones
    pipeline = relationship("PipelineMLOps")
    modelo = relationship("ModeloIA")

class MonitoreoModelo(Base):
    __tablename__ = "monitoreo_modelos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Métricas de rendimiento
    accuracy_produccion = Column(Float)
    precision_produccion = Column(Float)
    recall_produccion = Column(Float)
    f1_score_produccion = Column(Float)
    
    # Drift y degradación
    drift_datos = Column(Float)
    drift_concepto = Column(Float)
    score_degradacion = Column(Float)
    
    # Uso del modelo
    solicitudes_totales = Column(Integer, default=0)
    solicitudes_exitosas = Column(Integer, default=0)
    tasa_error = Column(Float)
    latencia_promedio = Column(Float)
    
    # Timestamps
    fecha_monitoreo = Column(DateTime(timezone=True), server_default=func.now())
    periodo_muestreo = Column(String(50))  # 'HOURLY', 'DAILY', 'WEEKLY'
    
    modelo = relationship("ModeloIA")