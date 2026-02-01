"""
Módulo de base de datos para el Asistente Inteligente de Emprendimiento
"""

from .database1 import SessionLocal, engine, get_db
from .models import (
    Base,
    Usuario, Rol, Permiso,
    Pais, Departamento, Ciudad, Barrio,
    Emprendedor, Negocio,
    ModeloIA, EvaluacionRiesgo, HistoricoModelo,
    Institucion, Oportunidad, InteraccionRecomendacion, 
    AplicacionOportunidad, Recomendacion,
    ConfiguracionPrivacidad, PoliticaPrivacidad, AceptacionPolitica,
    Consentimiento, DocumentoNegocio, EmpleadoNegocio, HistorialFinanciero,
    Auditoria, SesionUsuario, CaracteristicaSistema, ConfiguracionSistema, LogSistema
)
from .models_xai import (
    EmbeddingsCaracteristicas, ExplicacionContrafactual, 
    MetricasEquidad, AuditoriaExplicabilidad, SHAPAnalysis
)
from .models_synthetic import (
    DatosSinteticos, GeneradorSintetico, CalidadDatosSinteticos, BalanceoSesgo
)
from .models_mlops import (
    VersionModeloMLflow, PipelineMLOps, EjecucionPipeline, MonitoreoModelo
)

# Importar todos los repositorios
from .repositories import (
    usuario_repository,
    emprendedor_repository,
    negocio_repository,
    evaluacion_repository,
    oportunidad_repository,
    xai_repository,
    mlops_repository
)

__all__ = [
    # Configuración de base de datos
    'SessionLocal', 'engine', 'get_db', 'Base',
    
    # Modelos principales
    'Usuario', 'Rol', 'Permiso',
    'Pais', 'Departamento', 'Ciudad', 'Barrio',
    'Emprendedor', 'Negocio',
    'ModeloIA', 'EvaluacionRiesgo', 'HistoricoModelo',
    'Institucion', 'Oportunidad', 'InteraccionRecomendacion',
    'AplicacionOportunidad', 'Recomendacion',
    'ConfiguracionPrivacidad', 'PoliticaPrivacidad', 'AceptacionPolitica',
    'Consentimiento', 'DocumentoNegocio', 'EmpleadoNegocio', 'HistorialFinanciero',
    'Auditoria', 'SesionUsuario', 'CaracteristicaSistema', 'ConfiguracionSistema', 'LogSistema',
    
    # Modelos XAI
    'EmbeddingsCaracteristicas', 'ExplicacionContrafactual',
    'MetricasEquidad', 'AuditoriaExplicabilidad', 'SHAPAnalysis',
    
    # Modelos Synthetic Data
    'DatosSinteticos', 'GeneradorSintetico', 'CalidadDatosSinteticos', 'BalanceoSesgo',
    
    # Modelos MLOps
    'VersionModeloMLflow', 'PipelineMLOps', 'EjecucionPipeline', 'MonitoreoModelo',
    
    # Repositorios
    'usuario_repository',
    'emprendedor_repository', 
    'negocio_repository',
    'evaluacion_repository',
    'oportunidad_repository',
    'xai_repository',
    'mlops_repository'
]

# Información de versión del módulo
__version__ = '2.0.0'
__author__ = 'Equipo de Desarrollo - Asistente Inteligente para Emprendimiento'
__description__ = 'Módulo de base de datos para el sistema de recomendación híbrido con explicabilidad'