from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from base_datos.conexion import obtener_bd
from nucleo.seguridad import obtener_usuario_activo
from base_datos.modelos import Usuario
from servicios.servicio_xai import ServicioXAI
from servicios.servicio_perfil import ServicioPerfil
from esquemas.esquemas_xai import (
    ExplicacionCompleta,
    SolicitudFeedbackXAI
)

enrutador = APIRouter(prefix="/xai", tags=["Explicabilidad"])

servicio_xai = ServicioXAI()
servicio_perfil = ServicioPerfil()

@enrutador.get("/explicacion/{evaluacion_id}", response_model=dict)
def obtener_explicacion(
    evaluacion_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene explicacion completa de una evaluacion de riesgo
    """
    from base_datos.modelos import EvaluacionRiesgo
    
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    evaluacion = bd.query(EvaluacionRiesgo).filter(
        EvaluacionRiesgo.id == evaluacion_id,
        EvaluacionRiesgo.emprendedor_id == emprendedor.id
    ).first()
    
    if not evaluacion:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Evaluacion no encontrada")
    
    explicacion = servicio_xai.generar_explicacion_completa(bd, evaluacion_id)
    
    return explicacion

@enrutador.post("/feedback", status_code=status.HTTP_201_CREATED)
def registrar_feedback(
    solicitud: SolicitudFeedbackXAI,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Registra feedback del usuario sobre la explicacion
    """
    from base_datos.modelos import EvaluacionRiesgo
    
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    evaluacion = bd.query(EvaluacionRiesgo).filter(
        EvaluacionRiesgo.id == solicitud.evaluacion_riesgo_id,
        EvaluacionRiesgo.emprendedor_id == emprendedor.id
    ).first()
    
    if not evaluacion:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Evaluacion no encontrada")
    
    auditoria = servicio_xai.registrar_feedback(
        bd,
        solicitud.evaluacion_riesgo_id,
        solicitud.claridad_explicacion,
        solicitud.utilidad_explicacion,
        solicitud.confianza_explicacion,
        solicitud.accionabilidad_explicacion,
        solicitud.comentarios,
        solicitud.entendio_recomendaciones
    )
    
    return {
        "mensaje": "Feedback registrado exitosamente",
        "auditoria_id": auditoria.id
    }