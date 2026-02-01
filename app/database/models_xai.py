# database/models_xai.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .models import Base

class EmbeddingsCaracteristicas(Base):
    __tablename__ = "embeddings_caracteristicas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluacion_riesgo_id = Column(Integer, ForeignKey("evaluaciones_riesgo.id"))
    
    # Embeddings generados por la red neuronal
    embedding_categoricas = Column(JSON)  # Embeddings de variables categóricas
    embedding_final = Column(JSON)        # Embedding concatenado final
    
    # Metadatos
    modelo_embedding = Column(String(100))
    dimension_embedding = Column(Integer)
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    
    evaluacion = relationship("EvaluacionRiesgo", back_populates="embeddings")

class ExplicacionContrafactual(Base):
    __tablename__ = "explicaciones_contrafactuales"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluacion_riesgo_id = Column(Integer, ForeignKey("evaluaciones_riesgo.id"))
    
    # Escenario contrafactual
    caracteristicas_originales = Column(JSON)
    caracteristicas_modificadas = Column(JSON)
    cambios_sugeridos = Column(JSON)
    
    # Resultados del escenario
    categoria_original = Column(String(50))
    categoria_contrafactual = Column(String(50))
    puntaje_original = Column(Float)
    puntaje_contrafactual = Column(Float)
    mejora_puntaje = Column(Float)
    
    # Acciones específicas
    acciones_recomendadas = Column(JSON)
    impacto_acciones = Column(JSON)
    dificultad_implementacion = Column(String(50))  # 'BAJA', 'MEDIA', 'ALTA'
    
    # Metadata
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    algoritmo_contrafactual = Column(String(100))
    
    evaluacion = relationship("EvaluacionRiesgo")

class MetricasEquidad(Base):
    __tablename__ = "metricas_equidad"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Variables protegidas analizadas
    variable_protegida = Column(String(100))
    grupos_analizados = Column(JSON)
    
    # Métricas de equidad
    disparate_impact = Column(Float)
    igualdad_oportunidades = Column(Float)
    igualdad_trato = Column(Float)
    paridad_demografica = Column(Float)
    
    # Resultados por grupo
    metricas_por_grupo = Column(JSON)
    brechas_deteccion = Column(JSON)
    
    # Evaluación
    cumple_umbral_equidad = Column(Boolean)
    umbral_equidad = Column(Float, default=0.8)
    recomendaciones_mitigacion = Column(JSON)
    
    # Timestamps
    fecha_evaluacion = Column(DateTime(timezone=True), server_default=func.now())
    
    modelo = relationship("ModeloIA")

class AuditoriaExplicabilidad(Base):
    __tablename__ = "auditoria_explicabilidad"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluacion_riesgo_id = Column(Integer, ForeignKey("evaluaciones_riesgo.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"))
    
    # Evaluación de la explicación
    claridad_explicacion = Column(Integer)  # 1-5
    utilidad_explicacion = Column(Integer)  # 1-5
    confianza_explicacion = Column(Integer) # 1-5
    accionabilidad_explicacion = Column(Integer) # 1-5
    
    # Feedback cualitativo
    comentarios = Column(Text)
    sugerencias_mejora = Column(Text)
    entendio_recomendaciones = Column(Boolean)
    
    # Metadata
    fecha_auditoria = Column(DateTime(timezone=True), server_default=func.now())
    contexto_uso = Column(String(100))  # 'TOMA_DECISIONES', 'AUDITORIA', 'CAPACITACION'
    
    evaluacion = relationship("EvaluacionRiesgo")
    usuario = relationship("Usuario")

class SHAPAnalysis(Base):
    __tablename__ = "shap_analysis"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Análisis global SHAP
    importancia_global = Column(JSON)
    dependencias_caracteristicas = Column(JSON)
    interacciones_caracteristicas = Column(JSON)
    
    # Valores SHAP
    valores_shap_base = Column(JSON)
    expected_value = Column(Float)
    
    # Métricas de consistencia
    consistencia_explicaciones = Column(Float)
    estabilidad_shap = Column(Float)
    
    # Timestamps
    fecha_analisis = Column(DateTime(timezone=True), server_default=func.now())
    tamaño_muestra = Column(Integer)
    
    modelo = relationship("ModeloIA")