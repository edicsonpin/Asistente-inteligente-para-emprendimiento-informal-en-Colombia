from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import Optional, List

from database.models import Usuario, Emprendedor, Negocio
from schemas.esquemas_perfil import CrearEmprendedor, CrearNegocio, ActualizarNegocio
from nucleo.excepciones import NoEncontradoExcepcion

class ServicioPerfil:
    
    @staticmethod
    def obtener_perfil_emprendedor(bd: Session, usuario_id: int) -> Optional[Emprendedor]:
        emprendedor = bd.query(Emprendedor).options(
            joinedload(Emprendedor.negocios),
            joinedload(Emprendedor.pais_residencia),
            joinedload(Emprendedor.ciudad_residencia)
        ).filter(Emprendedor.usuario_id == usuario_id).first()
        
        return emprendedor
    
    @staticmethod
    def crear_perfil_emprendedor(
        bd: Session, 
        usuario_id: int, 
        datos: CrearEmprendedor
    ) -> Emprendedor:
        emprendedor_existente = bd.query(Emprendedor).filter(
            Emprendedor.usuario_id == usuario_id
        ).first()
        
        if emprendedor_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya tiene un perfil de emprendedor"
            )
        
        nuevo_emprendedor = Emprendedor(
            usuario_id=usuario_id,
            biografia=datos.biografia,
            habilidades=datos.habilidades,
            intereses=datos.intereses,
            pais_residencia_id=datos.pais_residencia_id,
            ciudad_residencia_id=datos.ciudad_residencia_id,
            barrio_residencia_id=datos.barrio_residencia_id,
            direccion_residencia=datos.direccion_residencia,
            estado="ACTIVO"
        )
        
        bd.add(nuevo_emprendedor)
        bd.commit()
        bd.refresh(nuevo_emprendedor)
        
        return nuevo_emprendedor
    
    @staticmethod
    def crear_negocio(
        bd: Session, 
        emprendedor_id: int, 
        datos: CrearNegocio
    ) -> Negocio:
        emprendedor = bd.query(Emprendedor).filter(Emprendedor.id == emprendedor_id).first()
        
        if not emprendedor:
            raise NoEncontradoExcepcion("Emprendedor no encontrado")
        
        nuevo_negocio = Negocio(
            emprendedor_id=emprendedor_id,
            nombre_comercial=datos.nombre_comercial,
            razon_social=datos.razon_social,
            sector_negocio=datos.sector_negocio,
            subsector=datos.subsector,
            descripcion_actividad=datos.descripcion_actividad,
            experiencia_sector=datos.experiencia_sector,
            meses_operacion=datos.meses_operacion,
            empleados_directos=datos.empleados_directos,
            ingresos_mensuales_promedio=datos.ingresos_mensuales_promedio,
            ciudad_id=datos.ciudad_id,
            barrio_id=datos.barrio_id,
            direccion_comercial=datos.direccion_comercial,
            telefono_comercial=datos.telefono_comercial,
            estado="ACTIVO"
        )
        
        bd.add(nuevo_negocio)
        bd.commit()
        bd.refresh(nuevo_negocio)
        
        return nuevo_negocio
    
    @staticmethod
    def actualizar_negocio(
        bd: Session,
        negocio_id: int,
        emprendedor_id: int,
        datos: ActualizarNegocio
    ) -> Negocio:
        negocio = bd.query(Negocio).filter(
            Negocio.id == negocio_id,
            Negocio.emprendedor_id == emprendedor_id
        ).first()
        
        if not negocio:
            raise NoEncontradoExcepcion("Negocio no encontrado")
        
        datos_actualizacion = datos.dict(exclude_unset=True)
        
        for campo, valor in datos_actualizacion.items():
            setattr(negocio, campo, valor)
        
        bd.commit()
        bd.refresh(negocio)
        
        return negocio
    
    @staticmethod
    def obtener_negocios_emprendedor(
        bd: Session,
        emprendedor_id: int
    ) -> List[Negocio]:
        negocios = bd.query(Negocio).filter(
            Negocio.emprendedor_id == emprendedor_id
        ).all()
        
        return negocios
    
    @staticmethod
    def obtener_negocio_por_id(
        bd: Session,
        negocio_id: int,
        emprendedor_id: int
    ) -> Negocio:
        negocio = bd.query(Negocio).filter(
            Negocio.id == negocio_id,
            Negocio.emprendedor_id == emprendedor_id
        ).first()
        
        if not negocio:
            raise NoEncontradoExcepcion("Negocio no encontrado")
        
        return negocio