from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExplicacionSHAP(BaseModel):
    valores_shap: Dict[str, float]
    valor_esperado: float
    caracteristicas_principales: List[Dict[str, any]]

class ExplicacionLIME(BaseModel):
    caracteristicas_locales: List[Dict[str, any]]
    puntaje_local: float

class ExplicacionContrafactual(BaseModel):
    caracteristicas_originales: Dict[str, any]
    caracteristicas_sugeridas: Dict[str, any]
    cambios_necesarios: List[Dict[str, any]]
    categoria_potencial: str
    puntaje_potencial: int
    mejora_esperada: int

class ExplicacionCompleta(BaseModel):
    evaluacion_id: int
    categoria_riesgo: str
    puntaje_riesgo: int
    explicacion_natural: str
    shap: Optional[ExplicacionSHAP]
    lime: Optional[ExplicacionLIME]
    contrafactual: Optional[ExplicacionContrafactual]

class SolicitudFeedbackXAI(BaseModel):
    evaluacion_riesgo_id: int
    claridad_explicacion: int = Field(..., ge=1, le=5)
    utilidad_explicacion: int = Field(..., ge=1, le=5)
    confianza_explicacion: int = Field(..., ge=1, le=5)
    accionabilidad_explicacion: int = Field(..., ge=1, le=5)
    comentarios: Optional[str] = None
    entendio_recomendaciones: bool