# database/models_synthetic.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .models import Base

class DatosSinteticos(Base):
    __tablename__ = "datos_sinteticos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Información del generador
    modelo_generador = Column(String(100))  # 'CTGAN', 'VariationalAutoencoder', etc.
    version_modelo = Column(String(20))
    tipo_dato = Column(String(50))  # 'entrenamiento', 'validacion', 'balanceo'
    
    # Información del dataset sintético
    caracteristicas_generadas = Column(JSON)
    tamaño_dataset = Column(Integer)
    parametros_generacion = Column(JSON)
    
    # Control de calidad
    score_calidad = Column(Float)
    metricas_similitud = Column(JSON)
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Uso y trazabilidad
    utilizado_entrenamiento = Column(Boolean, default=False)
    modelo_destino_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Relaciones
    modelo_origen = relationship("ModeloIA", foreign_keys=[modelo_ia_id])
    modelo_destino = relationship("ModeloIA", foreign_keys=[modelo_destino_id])

class GeneradorSintetico(Base):
    __tablename__ = "generadores_sinteticos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(50))  # 'CTGAN', 'VAE', 'GAN', 'Copula'
    descripcion = Column(Text)
    
    # Configuración del generador
    hiperparametros = Column(JSON)
    arquitectura = Column(JSON)
    caracteristicas_soportadas = Column(JSON)
    
    # Estado y rendimiento
    estado = Column(String(50), default="INACTIVO")
    accuracy_generacion = Column(Float)
    diversidad_generada = Column(Float)
    fidelidad_datos = Column(Float)
    
    # Uso y límites
    datos_generados_totales = Column(Integer, default=0)
    limite_generacion_diaria = Column(Integer, default=1000)
    ultima_generacion = Column(DateTime(timezone=True))
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    activo = Column(Boolean, default=True)

class CalidadDatosSinteticos(Base):
    __tablename__ = "calidad_datos_sinteticos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    datos_sinteticos_id = Column(Integer, ForeignKey("datos_sinteticos.id"))
    
    # Métricas de similitud estadística
    correlacion_promedio = Column(Float)
    distancia_distribucion = Column(Float)
    preservacion_varianza = Column(Float)
    
    # Métricas de utilidad
    score_utilidad = Column(Float)
    preservacion_relaciones = Column(Float)
    capacidad_generalizacion = Column(Float)
    
    # Métricas de privacidad
    riesgo_reenidentificacion = Column(Float)
    distancia_records_reales = Column(Float)
    score_privacidad = Column(Float)
    
    # Evaluación general
    score_calidad_total = Column(Float)
    cumple_umbral_calidad = Column(Boolean)
    recomendaciones_mejora = Column(JSON)
    
    # Timestamps
    fecha_evaluacion = Column(DateTime(timezone=True), server_default=func.now())
    
    datos_sinteticos = relationship("DatosSinteticos")

class BalanceoSesgo(Base):
    __tablename__ = "balanceo_sesgo"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    datos_sinteticos_id = Column(Integer, ForeignKey("datos_sinteticos.id"))
    
    # Información del balanceo
    variable_balanceo = Column(String(100))
    distribucion_original = Column(JSON)
    distribucion_objetivo = Column(JSON)
    distribucion_lograda = Column(JSON)
    
    # Métricas de balanceo
    mejora_balanceo = Column(Float)
    reduccion_sesgo = Column(Float)
    impacto_rendimiento = Column(Float)
    
    # Estrategia aplicada
    estrategia_balanceo = Column(String(100))  # 'oversampling', 'undersampling', 'smote'
    parametros_estrategia = Column(JSON)
    
    # Resultados
    metricas_antes = Column(JSON)
    metricas_despues = Column(JSON)
    mejora_equidad = Column(Float)
    
    # Timestamps
    fecha_balanceo = Column(DateTime(timezone=True), server_default=func.now())
    
    modelo = relationship("ModeloIA")
    datos_sinteticos = relationship("DatosSinteticos")