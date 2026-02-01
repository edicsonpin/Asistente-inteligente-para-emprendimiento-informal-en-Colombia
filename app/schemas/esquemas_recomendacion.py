from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class SolicitudRecomendacion(BaseModel):
    negocio_id: int
    limite: Optional[int] = Field(10, ge=1, le=50)
    incluir_explicacion: bool = True

class OportunidadRecomendada(BaseModel):
    id: int
    nombre: str
    tipo: str
    descripcion: str
    monto_minimo: float
    monto_maximo: float
    puntaje_compatibilidad: float
    nombre_institucion: str
    
    class Config:
        from_attributes = True

class RespuestaEvaluacionRiesgo(BaseModel):
    id: int
    categoria_riesgo: str
    puntaje_riesgo: int
    confianza_prediccion: float
    probabilidades: Dict[str, float]
    caracteristicas_importantes: List[Dict[str, any]]
    resumen_explicacion: Optional[str]
    fecha_evaluacion: datetime
    tiempo_procesamiento_ms: Optional[float]
    
    class Config:
        from_attributes = True

class RespuestaRecomendacion(BaseModel):
    evaluacion_riesgo: RespuestaEvaluacionRiesgo
    oportunidades_recomendadas: List[OportunidadRecomendada]
    total_oportunidades: int