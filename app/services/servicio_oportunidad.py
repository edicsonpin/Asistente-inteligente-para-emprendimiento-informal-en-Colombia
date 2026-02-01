from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.database.models import Oportunidad, Institucion
from nucleo.excepciones import NoEncontradoExcepcion

class ServicioOportunidad:
    
    def listar_oportunidades(
        self,
        bd: Session,
        sector: Optional[str] = None,
        tipo: Optional[str] = None,
        estado: str = "ACTIVA",
        limite: int = 50,
        desplazamiento: int = 0
    ) -> List[Oportunidad]:
        query = bd.query(Oportunidad).options(
            joinedload(Oportunidad.institucion)
        )
        
        if estado:
            query = query.filter(Oportunidad.estado == estado)
        
        if sector:
            query = query.filter(Oportunidad.sector_compatible == sector)
        
        if tipo:
            query = query.filter(Oportunidad.tipo == tipo)
        
        query = query.filter(Oportunidad.fecha_cierre >= datetime.now())
        
        oportunidades = query.offset(desplazamiento).limit(limite).all()
        
        return oportunidades
    
    def obtener_oportunidad(
        self,
        bd: Session,
        oportunidad_id: int
    ) -> Oportunidad:
        oportunidad = bd.query(Oportunidad).options(
            joinedload(Oportunidad.institucion)
        ).filter(Oportunidad.id == oportunidad_id).first()
        
        if not oportunidad:
            raise NoEncontradoExcepcion("Oportunidad no encontrada")
        
        oportunidad.vistas += 1
        bd.commit()
        
        return oportunidad
    
    def buscar_oportunidades(
        self,
        bd: Session,
        termino_busqueda: str,
        limite: int = 20
    ) -> List[Oportunidad]:
        termino = f"%{termino_busqueda}%"
        
        oportunidades = bd.query(Oportunidad).filter(
            Oportunidad.estado == "ACTIVA",
            (Oportunidad.nombre.ilike(termino) | 
             Oportunidad.descripcion.ilike(termino))
        ).limit(limite).all()
        
        return oportunidades