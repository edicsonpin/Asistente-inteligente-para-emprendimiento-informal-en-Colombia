# schemas/base.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime
from decimal import Decimal

class ModeloBase(BaseModel):
    """Schema base con configuración común"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class RespuestaBase(ModeloBase):
    """Schema base para respuestas API"""
    mensaje: str
    exito: bool = True
    datos: Optional[Any] = None

class PaginacionBase(ModeloBase):
    """Schema base para paginación"""
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class FiltrosBase(ModeloBase):
    """Schema base para filtros"""
    skip: int = 0
    limit: int = 100
    ordenar_por: Optional[str] = None
    descendente: bool = False

# Tipos comunes
class JSONSchema(ModeloBase):
    datos: Optional[Dict[str, Any]] = None