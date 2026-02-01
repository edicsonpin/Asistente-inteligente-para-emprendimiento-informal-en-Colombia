from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CrearEmprendedor(BaseModel):
    biografia: Optional[str] = None
    habilidades: Optional[List[str]] = None
    intereses: Optional[List[str]] = None
    pais_residencia_id: int
    ciudad_residencia_id: int
    barrio_residencia_id: Optional[int] = None
    direccion_residencia: Optional[str] = None

class CrearNegocio(BaseModel):
    nombre_comercial: str = Field(..., max_length=255)
    razon_social: Optional[str] = Field(None, max_length=255)
    sector_negocio: str
    subsector: Optional[str] = None
    descripcion_actividad: Optional[str] = None
    experiencia_sector: int = Field(0, ge=0)
    meses_operacion: int = Field(0, ge=0)
    empleados_directos: int = Field(0, ge=0)
    ingresos_mensuales_promedio: float = Field(0.0, ge=0)
    ciudad_id: int
    barrio_id: Optional[int] = None
    direccion_comercial: Optional[str] = None
    telefono_comercial: Optional[str] = None

class ActualizarNegocio(BaseModel):
    nombre_comercial: Optional[str] = None
    descripcion_actividad: Optional[str] = None
    experiencia_sector: Optional[int] = None
    meses_operacion: Optional[int] = None
    empleados_directos: Optional[int] = None
    empleados_indirectos: Optional[int] = None
    ingresos_mensuales_promedio: Optional[float] = None
    ingresos_anuales: Optional[float] = None
    capital_trabajo: Optional[float] = None
    telefono_comercial: Optional[str] = None

class RespuestaNegocio(BaseModel):
    id: int
    nombre_comercial: str
    sector_negocio: str
    meses_operacion: int
    empleados_directos: int
    ingresos_mensuales_promedio: float
    estado: str
    fecha_registro: datetime
    
    class Config:
        from_attributes = True

class PerfilEmprendedor(BaseModel):
    id: int
    biografia: Optional[str]
    experiencia_total: int
    habilidades: Optional[List[str]]
    estado: str
    negocios: List[RespuestaNegocio]
    
    class Config:
        from_attributes = True