from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from base_datos.conexion import obtener_bd
from nucleo.seguridad import obtener_usuario_activo
from base_datos.modelos import Usuario
from services.servicio_recomendacion import ServicioRecomendacion
from services.servicio_perfil import ServicioPerfil
from schemas.esquemas_recomendacion import (
    SolicitudRecomendacion,
    RespuestaRecomendacion
)

enrutador = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])

servicio_recomendacion = ServicioRecomendacion()
servicio_perfil = ServicioPerfil()

@enrutador.post("/generar", response_model=dict)
def generar_recomendacion(
    solicitud: SolicitudRecomendacion,
    tareas_fondo: BackgroundTasks,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Genera recomendaciones personalizadas para un negocio
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    negocio = servicio_perfil.obtener_negocio_por_id(
        bd,
        solicitud.negocio_id,
        emprendedor.id
    )
    
    resultado = servicio_recomendacion.generar_recomendacion(
        bd,
        solicitud.negocio_id,
        solicitud.limite,
        solicitud.incluir_explicacion
    )
    
    evaluacion = resultado["evaluacion_riesgo"]
    oportunidades = resultado["oportunidades"]
    
    respuesta = {
        "evaluacion_riesgo": {
            "id": evaluacion.id,
            "categoria_riesgo": evaluacion.categoria_riesgo,
            "puntaje_riesgo": evaluacion.puntaje_riesgo,
            "confianza_prediccion": evaluacion.confianza_prediccion,
            "probabilidades": {
                "MUY_BAJO": evaluacion.probabilidad_muy_bajo,
                "BAJO": evaluacion.probabilidad_bajo,
                "MEDIO": evaluacion.probabilidad_medio,
                "ALTO": evaluacion.probabilidad_alto,
                "MUY_ALTO": evaluacion.probabilidad_muy_alto
            },
            "caracteristicas_importantes": [],
            "resumen_explicacion": None,
            "fecha_evaluacion": evaluacion.fecha_evaluacion,
            "tiempo_procesamiento_ms": evaluacion.tiempo_procesamiento
        },
        "oportunidades_recomendadas": [
            {
                "id": oport.id,
                "nombre": oport.nombre,
                "tipo": oport.tipo.value if hasattr(oport.tipo, 'value') else oport.tipo,
                "descripcion": oport.descripcion or "",
                "monto_minimo": oport.monto_minimo or 0,
                "monto_maximo": oport.monto_maximo or 0,
                "puntaje_compatibilidad": 0.85,
                "nombre_institucion": oport.institucion.nombre if oport.institucion else "Sin institucion"
            }
            for oport in oportunidades
        ],
        "total_oportunidades": len(oportunidades)
    }
    
    return respuesta

@enrutador.get("/historial/{negocio_id}")
def obtener_historial_evaluaciones(
    negocio_id: int,
    limite: int = 10,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene historial de evaluaciones de riesgo para un negocio
    """
    from base_datos.modelos import EvaluacionRiesgo
    
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    evaluaciones = bd.query(EvaluacionRiesgo).filter(
        EvaluacionRiesgo.negocio_id == negocio_id,
        EvaluacionRiesgo.emprendedor_id == emprendedor.id
    ).order_by(EvaluacionRiesgo.fecha_evaluacion.desc()).limit(limite).all()
    
    return {
        "evaluaciones": [
            {
                "id": ev.id,
                "categoria_riesgo": ev.categoria_riesgo,
                "puntaje_riesgo": ev.puntaje_riesgo,
                "confianza_prediccion": ev.confianza_prediccion,
                "fecha_evaluacion": ev.fecha_evaluacion
            }
            for ev in evaluaciones
        ],
        "total": len(evaluaciones)
    }