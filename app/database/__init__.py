# database/__init__.py

# Importaciones CORREGIDAS - usar .config en lugar de .database
from .config2 import engine, Base, get_db, SessionLocal

# Importaciones de modelos principales
from .models import (
    Usuario, Rol, Permiso, Emprendedor, Negocio, 
    Pais, Departamento, Ciudad, Barrio,
    ModeloIA, EvaluacionRiesgo, HistoricoModelo,
    Institucion, Oportunidad, InteraccionRecomendacion,
    AplicacionOportunidad, Recomendacion,
    ConfiguracionPrivacidad, PoliticaPrivacidad, AceptacionPolitica,
    Consentimiento, DocumentoNegocio, EmpleadoNegocio, HistorialFinanciero,
    Auditoria, SesionUsuario, CaracteristicaSistema, ConfiguracionSistema, LogSistema
)


# Importaciones de modelos XAI
from .models_xai import (
    EmbeddingsCaracteristicas, ExplicacionContrafactual,
    MetricasEquidad, AuditoriaExplicabilidad, SHAPAnalysis
)

# Importaciones de modelos sintéticos
from .models_synthetic import (
    DatosSinteticos, GeneradorSintetico, 
    CalidadDatosSinteticos, BalanceoSesgo
)

# Importaciones de modelos MLOps
from .models_mlops import (
    VersionModeloMLflow, PipelineMLOps, 
    EjecucionPipeline, MonitoreoModelo
)

__all__ = [
    # Config
    "engine", "Base", "get_db", "SessionLocal",
    
    # Models principales
    "Usuario", "Rol", "Permiso", "Emprendedor", "Negocio",
    "Pais", "Departamento", "Ciudad", "Barrio",
    "ModeloIA", "EvaluacionRiesgo", "HistoricoModelo",
    "Institucion", "Oportunidad", "InteraccionRecomendacion",
    "AplicacionOportunidad", "Recomendacion",
    "ConfiguracionPrivacidad", "PoliticaPrivacidad", "AceptacionPolitica",
    "Consentimiento", "DocumentoNegocio", "EmpleadoNegocio", "HistorialFinanciero",
    "Auditoria", "SesionUsuario", "CaracteristicaSistema", "ConfiguracionSistema", "LogSistema",
    
    # Models XAI
    "EmbeddingsCaracteristicas", "ExplicacionContrafactual",
    "MetricasEquidad", "AuditoriaExplicabilidad", "SHAPAnalysis",
    
    # Models Synthetic
    "DatosSinteticos", "GeneradorSintetico",
    "CalidadDatosSinteticos", "BalanceoSesgo",
    
    # Models MLOps
    "VersionModeloMLflow", "PipelineMLOps",
    "EjecucionPipeline", "MonitoreoModelo"
]