from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from base_datos.conexion import obtener_bd
from nucleo.seguridad import obtener_usuario_activo
from base_datos.modelos import Usuario
from servicios.servicio_perfil import ServicioPerfil
from esquemas.esquemas_perfil import (
    CrearEmprendedor,
    CrearNegocio,
    ActualizarNegocio,
    PerfilEmprendedor,
    RespuestaNegocio
)

enrutador = APIRouter(prefix="/perfil", tags=["Perfil"])

servicio_perfil = ServicioPerfil()

@enrutador.post("/emprendedor", response_model=PerfilEmprendedor, status_code=status.HTTP_201_CREATED)
def crear_perfil_emprendedor(
    datos: CrearEmprendedor,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Crea perfil de emprendedor para el usuario autenticado
    """
    emprendedor = servicio_perfil.crear_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id,
        datos
    )
    return emprendedor

@enrutador.get("/emprendedor", response_model=PerfilEmprendedor)
def obtener_perfil_emprendedor(
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene perfil completo del emprendedor autenticado
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    return emprendedor

@enrutador.post("/negocio", response_model=RespuestaNegocio, status_code=status.HTTP_201_CREATED)
def crear_negocio(
    datos: CrearNegocio,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Crea un nuevo negocio para el emprendedor
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Debe crear un perfil de emprendedor primero")
    
    negocio = servicio_perfil.crear_negocio(bd, emprendedor.id, datos)
    return negocio

@enrutador.get("/negocios", response_model=List[RespuestaNegocio])
def listar_negocios(
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Lista todos los negocios del emprendedor autenticado
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        return []
    
    negocios = servicio_perfil.obtener_negocios_emprendedor(bd, emprendedor.id)
    return negocios

@enrutador.get("/negocio/{negocio_id}", response_model=RespuestaNegocio)
def obtener_negocio(
    negocio_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Obtiene detalles de un negocio especifico
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    negocio = servicio_perfil.obtener_negocio_por_id(bd, negocio_id, emprendedor.id)
    return negocio

@enrutador.put("/negocio/{negocio_id}", response_model=RespuestaNegocio)
def actualizar_negocio(
    negocio_id: int,
    datos: ActualizarNegocio,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_activo)
):
    """
    Actualiza informacion de un negocio
    """
    emprendedor = servicio_perfil.obtener_perfil_emprendedor(
        bd,
        usuario_actual.usuario_id
    )
    
    if not emprendedor:
        from nucleo.excepciones import NoEncontradoExcepcion
        raise NoEncontradoExcepcion("Perfil de emprendedor no encontrado")
    
    negocio = servicio_perfil.actualizar_negocio(
        bd,
        negocio_id,
        emprendedor.id,
        datos
    )
    return negocio