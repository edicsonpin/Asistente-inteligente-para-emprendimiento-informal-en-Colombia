from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from base_datos.conexion import obtener_bd
from nucleo.seguridad import obtener_usuario_activo
from base_datos.modelos import Usuario
from services.servicio_oportunidad import ServicioOportunidad

enrutador = APIRouter(prefix="/oportunidades", tags=["Oportunidades"])

servicio_oportunidad = ServicioOportunidad()

@enrutador.get("/listar")
def listar_oportunidades(
    sector: Optional[str] = None,
    tipo: Optional[str] = None,
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Lista oportunidades disponibles con filtros opcionales
    """
    oportunidades = servicio_oportunidad.listar_oportunidades(
        bd,
        sector=sector,
        tipo=tipo,
        limite=limite,
        desplazamiento=desplazamiento
    )
    
    return {
        "oportunidades": [
            {
                "id": oport.id,
                "nombre": oport.nombre,
                "tipo": oport.tipo.value if hasattr(oport.tipo, 'value') else oport.tipo,
                "descripcion": oport.descripcion or "",
                "sector_compatible": oport.sector_compatible.value if hasattr(oport.sector_compatible, 'value') else oport.sector_compatible,
                "monto_minimo": oport.monto_minimo or 0,
                "monto_maximo": oport.monto_maximo or 0,
                "fecha_cierre": oport.fecha_cierre,
                "institucion": oport.institucion.nombre if oport.institucion else "Sin institucion"
            }
            for oport in oportunidades
        ],
        "total": len(oportunidades)
    }

@enrutador.get("/{oportunidad_id}")
def obtener_detalle_oportunidad(
    oportunidad_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene detalle completo de una oportunidad
    """
    oportunidad = servicio_oportunidad.obtener_oportunidad(bd, oportunidad_id)
    
    return {
        "id": oportunidad.id,
        "nombre": oportunidad.nombre,
        "tipo": oportunidad.tipo.value if hasattr(oportunidad.tipo, 'value') else oportunidad.tipo,
        "descripcion": oportunidad.descripcion or "",
        "beneficios": oportunidad.beneficios or "",
        "requisitos": oportunidad.requisitos or "",
        "sector_compatible": oportunidad.sector_compatible.value if hasattr(oportunidad.sector_compatible, 'value') else oportunidad.sector_compatible,
        "monto_minimo": oportunidad.monto_minimo or 0,
        "monto_maximo": oportunidad.monto_maximo or 0,
        "tasa_interes": oportunidad.tasa_interes,
        "fecha_apertura": oportunidad.fecha_apertura,
        "fecha_cierre": oportunidad.fecha_cierre,
        "estado": oportunidad.estado.value if hasattr(oportunidad.estado, 'value') else oportunidad.estado,
        "vistas": oportunidad.vistas,
        "contacto_nombre": oportunidad.contacto_nombre,
        "contacto_email": oportunidad.contacto_email,
        "contacto_telefono": oportunidad.contacto_telefono,
        "url_aplicacion": oportunidad.url_aplicacion,
        "institucion": {
            "id": oportunidad.institucion.id,
            "nombre": oportunidad.institucion.nombre,
            "tipo": oportunidad.institucion.tipo
        } if oportunidad.institucion else None
    }

@enrutador.get("/buscar/")
def buscar_oportunidades(
    q: str = Query(..., min_length=3),
    limite: int = Query(20, ge=1, le=50),
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Busca oportunidades por termino
    """
    oportunidades = servicio_oportunidad.buscar_oportunidades(
        bd,
        q,
        limite
    )
    
    return {
        "termino_busqueda": q,
        "resultados": [
            {
                "id": oport.id,
                "nombre": oport.nombre,
                "tipo": oport.tipo.value if hasattr(oport.tipo, 'value') else oport.tipo,
                "descripcion": oport.descripcion or ""
            }
            for oport in oportunidades
        ],
        "total": len(oportunidades)
    }