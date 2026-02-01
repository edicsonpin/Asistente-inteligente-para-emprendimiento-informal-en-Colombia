from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from base_datos.conexion import obtener_bd
from nucleo.seguridad import obtener_usuario_activo
from base_datos.modelos import Usuario

enrutador = APIRouter(prefix="/mlops", tags=["MLOps"])

@enrutador.get("/modelo/estado")
def obtener_estado_modelo(
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene estado actual del modelo en produccion
    """
    from base_datos.modelos import ModeloIA
    
    modelo_activo = bd.query(ModeloIA).filter(
        ModeloIA.es_produccion == True,
        ModeloIA.activo == True
    ).first()
    
    if not modelo_activo:
        return {
            "estado": "SIN_MODELO",
            "mensaje": "No hay modelo activo en produccion"
        }
    
    return {
        "estado": "ACTIVO",
        "modelo_id": modelo_activo.id,
        "nombre": modelo_activo.nombre,
        "version": modelo_activo.version,
        "tipo": modelo_activo.tipo.value if hasattr(modelo_activo.tipo, 'value') else modelo_activo.tipo,
        "accuracy": modelo_activo.accuracy,
        "precision": modelo_activo.precision,
        "recall": modelo_activo.recall,
        "f1_score": modelo_activo.f1_score,
        "fecha_entrenamiento": modelo_activo.fecha_entrenamiento,
        "fecha_actualizacion": modelo_activo.fecha_actualizacion
    }

@enrutador.get("/modelo/metricas/{modelo_id}")
def obtener_metricas_modelo(
    modelo_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene metricas detalladas de un modelo
    """
    from base_datos.modelos import ModeloIA, HistoricoModelo
    
    modelo = bd.query(ModeloIA).filter(ModeloIA.id == modelo_id).first()
    
    if not modelo:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Modelo no encontrado")
    
    historico = bd.query(HistoricoModelo).filter(
        HistoricoModelo.modelo_ia_id == modelo_id
    ).order_by(HistoricoModelo.fecha_entrenamiento.desc()).first()
    
    return {
        "modelo_id": modelo.id,
        "nombre": modelo.nombre,
        "metricas_actuales": {
            "accuracy": modelo.accuracy,
            "precision": modelo.precision,
            "recall": modelo.recall,
            "f1_score": modelo.f1_score
        },
        "historico_reciente": {
            "accuracy": historico.accuracy if historico else None,
            "precision": historico.precision if historico else None,
            "recall": historico.recall if historico else None,
            "f1_score": historico.f1_score if historico else None,
            "fecha_entrenamiento": historico.fecha_entrenamiento if historico else None
        } if historico else None
    }

@enrutador.get("/monitoreo/drift")
def obtener_metricas_drift(
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene metricas de drift del modelo activo
    """
    from base_datos.modelos import ModeloIA
    from base_datos.modelos_mlops import MonitoreoModelo
    
    modelo_activo = bd.query(ModeloIA).filter(
        ModeloIA.es_produccion == True,
        ModeloIA.activo == True
    ).first()
    
    if not modelo_activo:
        return {
            "estado": "SIN_MODELO",
            "mensaje": "No hay modelo activo para monitorear"
        }
    
    monitoreo = bd.query(MonitoreoModelo).filter(
        MonitoreoModelo.modelo_ia_id == modelo_activo.id
    ).order_by(MonitoreoModelo.fecha_monitoreo.desc()).first()
    
    if not monitoreo:
        return {
            "estado": "SIN_DATOS",
            "mensaje": "No hay datos de monitoreo disponibles"
        }
    
    umbral_drift = 0.15
    requiere_atencion = (
        monitoreo.drift_datos > umbral_drift or
        monitoreo.drift_concepto > umbral_drift
    )
    
    return {
        "modelo_id": modelo_activo.id,
        "fecha_monitoreo": monitoreo.fecha_monitoreo,
        "metricas_produccion": {
            "accuracy": monitoreo.accuracy_produccion,
            "precision": monitoreo.precision_produccion,
            "recall": monitoreo.recall_produccion,
            "f1_score": monitoreo.f1_score_produccion
        },
        "drift": {
            "drift_datos": monitoreo.drift_datos,
            "drift_concepto": monitoreo.drift_concepto,
            "score_degradacion": monitoreo.score_degradacion,
            "umbral": umbral_drift,
            "requiere_atencion": requiere_atencion
        },
        "uso": {
            "solicitudes_totales": monitoreo.solicitudes_totales,
            "solicitudes_exitosas": monitoreo.solicitudes_exitosas,
            "tasa_error": monitoreo.tasa_error,
            "latencia_promedio_ms": monitoreo.latencia_promedio
        }
    }