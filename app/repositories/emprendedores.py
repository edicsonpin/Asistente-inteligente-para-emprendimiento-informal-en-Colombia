# repositories/emprendedores.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from database.models import Emprendedor, Usuario, Pais, Ciudad, Barrio
from schemas.emprendedores import EmprendedorCreate, EmprendedorUpdate
from repositories.base import CRUDBase

class EmprendedorRepository(CRUDBase[Emprendedor, EmprendedorCreate, EmprendedorUpdate]):
    def __init__(self):
        super().__init__(Emprendedor)

    def get_by_usuario(self, db: Session, usuario_id: int) -> Optional[Emprendedor]:
        return db.query(Emprendedor).filter(Emprendedor.usuario_id == usuario_id).first()

    def get_with_usuario(self, db: Session, emprendedor_id: int) -> Optional[Emprendedor]:
        return db.query(Emprendedor).filter(Emprendedor.id == emprendedor_id).first()

    def get_with_ubicacion(self, db: Session, emprendedor_id: int) -> Optional[Emprendedor]:
        return db.query(Emprendedor).\
            outerjoin(Pais, Emprendedor.pais_residencia_id == Pais.pais_id).\
            outerjoin(Ciudad, Emprendedor.ciudad_residencia_id == Ciudad.ciudad_id).\
            outerjoin(Barrio, Emprendedor.barrio_residencia_id == Barrio.barrio_id).\
            filter(Emprendedor.id == emprendedor_id).first()

    def create(self, db: Session, *, obj_in: EmprendedorCreate) -> Emprendedor:
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.usuario_id == obj_in.usuario_id).first()
        if not usuario:
            raise ValueError("El usuario especificado no existe")

        # Verificar que no existe ya un emprendedor para este usuario
        existente = self.get_by_usuario(db, obj_in.usuario_id)
        if existente:
            raise ValueError("Ya existe un emprendedor para este usuario")

        # Verificar ubicación si se proporciona
        if obj_in.barrio_residencia_id:
            barrio = db.query(Barrio).filter(Barrio.barrio_id == obj_in.barrio_residencia_id).first()
            if not barrio:
                raise ValueError("El barrio especificado no existe")
            if barrio.ciudad_id != obj_in.ciudad_residencia_id:
                raise ValueError("El barrio no pertenece a la ciudad especificada")

        if obj_in.ciudad_residencia_id:
            ciudad = db.query(Ciudad).filter(Ciudad.ciudad_id == obj_in.ciudad_residencia_id).first()
            if not ciudad:
                raise ValueError("La ciudad especificada no existe")
            if ciudad.departamento.pais_id != obj_in.pais_residencia_id:
                raise ValueError("La ciudad no pertenece al país especificado")

        if obj_in.pais_residencia_id:
            pais = db.query(Pais).filter(Pais.pais_id == obj_in.pais_residencia_id).first()
            if not pais:
                raise ValueError("El país especificado no existe")

        db_obj = Emprendedor(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Emprendedor, obj_in: EmprendedorUpdate) -> Emprendedor:
        update_data = obj_in.dict(exclude_unset=True)
        
        # Validar ubicación si se actualiza
        if 'barrio_residencia_id' in update_data or 'ciudad_residencia_id' in update_data or 'pais_residencia_id' in update_data:
            barrio_id = update_data.get('barrio_residencia_id', db_obj.barrio_residencia_id)
            ciudad_id = update_data.get('ciudad_residencia_id', db_obj.ciudad_residencia_id)
            pais_id = update_data.get('pais_residencia_id', db_obj.pais_residencia_id)

            if barrio_id and ciudad_id:
                barrio = db.query(Barrio).filter(Barrio.barrio_id == barrio_id).first()
                if not barrio or barrio.ciudad_id != ciudad_id:
                    raise ValueError("El barrio no pertenece a la ciudad especificada")

            if ciudad_id and pais_id:
                ciudad = db.query(Ciudad).filter(Ciudad.ciudad_id == ciudad_id).first()
                if not ciudad or ciudad.departamento.pais_id != pais_id:
                    raise ValueError("La ciudad no pertenece al país especificado")

        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def buscar_por_habilidad(self, db: Session, habilidad: str, skip: int = 0, limit: int = 100) -> List[Emprendedor]:
        return db.query(Emprendedor).\
            filter(Emprendedor.habilidades.contains([habilidad])).\
            offset(skip).limit(limit).all()

    def buscar_por_interes(self, db: Session, interes: str, skip: int = 0, limit: int = 100) -> List[Emprendedor]:
        return db.query(Emprendedor).\
            filter(Emprendedor.intereses.contains([interes])).\
            offset(skip).limit(limit).all()

    def buscar_por_estado(self, db: Session, estado: str, skip: int = 0, limit: int = 100) -> List[Emprendedor]:
        return db.query(Emprendedor).\
            filter(Emprendedor.estado == estado).\
            offset(skip).limit(limit).all()

    def buscar_por_ubicacion(self, db: Session, ciudad_id: Optional[int] = None, pais_id: Optional[int] = None) -> List[Emprendedor]:
        query = db.query(Emprendedor)
        
        if ciudad_id:
            query = query.filter(Emprendedor.ciudad_residencia_id == ciudad_id)
        elif pais_id:
            query = query.filter(Emprendedor.pais_residencia_id == pais_id)
        
        return query.all()

    def get_estadisticas(self, db: Session, emprendedor_id: int) -> Dict[str, Any]:
        emprendedor = self.get(db, emprendedor_id)
        if not emprendedor:
            raise ValueError("Emprendedor no encontrado")

        # Aquí puedes agregar lógica para calcular estadísticas
        # como número de negocios, evaluaciones, etc.
        return {
            "emprendedor_id": emprendedor_id,
            "total_negocios": len(emprendedor.negocios) if hasattr(emprendedor, 'negocios') else 0,
            "experiencia_total": emprendedor.experiencia_total,
            "estado": emprendedor.estado,
            "score_completitud": emprendedor.score_completitud
        }

    def actualizar_score_completitud(self, db: Session, emprendedor_id: int) -> Emprendedor:
        emprendedor = self.get(db, emprendedor_id)
        if not emprendedor:
            raise ValueError("Emprendedor no encontrado")

        # Lógica para calcular el score de completitud
        campos_obligatorios = [
            emprendedor.biografia,
            emprendedor.habilidades,
            emprendedor.intereses,
            emprendedor.direccion_residencia
        ]
        
        campos_completados = sum(1 for campo in campos_obligatorios if campo)
        score = (campos_completados / len(campos_obligatorios)) * 100
        
        emprendedor.score_completitud = score
        db.commit()
        db.refresh(emprendedor)
        return emprendedor

emprendedor_repository = EmprendedorRepository()