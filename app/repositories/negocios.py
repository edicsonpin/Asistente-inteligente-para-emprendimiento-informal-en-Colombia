# repositories/negocios.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from decimal import Decimal
from database.models import Negocio, Emprendedor, Pais, Ciudad, Barrio, EvaluacionRiesgo
from schemas.negocios import NegocioCreate, NegocioUpdate
from repositories.base import CRUDBase

class NegocioRepository(CRUDBase[Negocio, NegocioCreate, NegocioUpdate]):
    def __init__(self):
        super().__init__(Negocio)

    def get_by_emprendedor(self, db: Session, emprendedor_id: int) -> List[Negocio]:
        return db.query(Negocio).filter(Negocio.emprendedor_id == emprendedor_id).all()

    def get_negocio_principal(self, db: Session, emprendedor_id: int) -> Optional[Negocio]:
        return db.query(Negocio).filter(
            Negocio.emprendedor_id == emprendedor_id,
            Negocio.es_negocio_principal == True
        ).first()

    def get_with_emprendedor(self, db: Session, negocio_id: int) -> Optional[Negocio]:
        return db.query(Negocio).filter(Negocio.id == negocio_id).first()

    def get_with_ubicacion(self, db: Session, negocio_id: int) -> Optional[Negocio]:
        return db.query(Negocio).\
            outerjoin(Pais, Negocio.pais_id == Pais.pais_id).\
            outerjoin(Ciudad, Negocio.ciudad_id == Ciudad.ciudad_id).\
            outerjoin(Barrio, Negocio.barrio_id == Barrio.barrio_id).\
            filter(Negocio.id == negocio_id).first()

    def get_with_evaluaciones(self, db: Session, negocio_id: int) -> Optional[Negocio]:
        return db.query(Negocio).filter(Negocio.id == negocio_id).first()

    def create(self, db: Session, *, obj_in: NegocioCreate) -> Negocio:
        # Verificar que el emprendedor existe
        emprendedor = db.query(Emprendedor).filter(Emprendedor.id == obj_in.emprendedor_id).first()
        if not emprendedor:
            raise ValueError("El emprendedor especificado no existe")

        # Si es negocio principal, desmarcar otros negocios principales del mismo emprendedor
        if obj_in.es_negocio_principal:
            negocios_principales = self.get_negocio_principal(db, obj_in.emprendedor_id)
            if negocios_principales:
                negocios_principales.es_negocio_principal = False
                db.commit()

        # Verificar ubicación si se proporciona
        if obj_in.barrio_id:
            barrio = db.query(Barrio).filter(Barrio.barrio_id == obj_in.barrio_id).first()
            if not barrio:
                raise ValueError("El barrio especificado no existe")

        if obj_in.ciudad_id:
            ciudad = db.query(Ciudad).filter(Ciudad.ciudad_id == obj_in.ciudad_id).first()
            if not ciudad:
                raise ValueError("La ciudad especificada no existe")

        if obj_in.pais_id:
            pais = db.query(Pais).filter(Pais.pais_id == obj_in.pais_id).first()
            if not pais:
                raise ValueError("El país especificado no existe")

        db_obj = Negocio(**obj_in.dict())
        
        # Calcular edad del negocio si se proporciona fecha de constitución
        if obj_in.fecha_constitucion:
            from datetime import datetime
            hoy = datetime.now()
            meses = (hoy.year - obj_in.fecha_constitucion.year) * 12 + (hoy.month - obj_in.fecha_constitucion.month)
            db_obj.edad_negocio = max(0, meses)

        # Calcular ratios financieros
        if obj_in.ingresos_anuales > 0:
            db_obj.ratio_deuda_ingresos = float(obj_in.deuda_existente) / float(obj_in.ingresos_anuales)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Negocio, obj_in: NegocioUpdate) -> Negocio:
        update_data = obj_in.dict(exclude_unset=True)
        
        # Si se marca como negocio principal, desmarcar otros
        if update_data.get('es_negocio_principal', False):
            negocios_principales = self.get_negocio_principal(db, db_obj.emprendedor_id)
            if negocios_principales and negocios_principales.id != db_obj.id:
                negocios_principales.es_negocio_principal = False

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Recalcular métricas si se actualizan campos financieros
        campos_financieros = ['deuda_existente', 'ingresos_anuales', 'activos_totales', 'pasivos_totales']
        if any(campo in update_data for campo in campos_financieros):
            if db_obj.ingresos_anuales > 0:
                db_obj.ratio_deuda_ingresos = float(db_obj.deuda_existente) / float(db_obj.ingresos_anuales)
            
            if db_obj.activos_totales > 0:
                db_obj.rentabilidad_estimada = float(db_obj.ingresos_anuales - db_obj.deuda_existente) / float(db_obj.activos_totales) * 100

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def buscar_por_sector(self, db: Session, sector: str, skip: int = 0, limit: int = 100) -> List[Negocio]:
        return db.query(Negocio).\
            filter(Negocio.sector_negocio == sector).\
            offset(skip).limit(limit).all()

    def buscar_por_ubicacion(self, db: Session, ciudad_id: Optional[int] = None, pais_id: Optional[int] = None) -> List[Negocio]:
        query = db.query(Negocio)
        
        if ciudad_id:
            query = query.filter(Negocio.ciudad_id == ciudad_id)
        elif pais_id:
            query = query.filter(Negocio.pais_id == pais_id)
        
        return query.all()

    def buscar_mipymes(self, db: Session, es_mipyme: bool = True, skip: int = 0, limit: int = 100) -> List[Negocio]:
        return db.query(Negocio).\
            filter(Negocio.es_mipyme == es_mipyme).\
            offset(skip).limit(limit).all()

    def get_estadisticas_negocio(self, db: Session, negocio_id: int) -> Dict[str, Any]:
        negocio = self.get(db, negocio_id)
        if not negocio:
            raise ValueError("Negocio no encontrado")

        # Obtener evaluaciones de riesgo
        evaluaciones = db.query(EvaluacionRiesgo).filter(EvaluacionRiesgo.negocio_id == negocio_id).all()
        
        return {
            "negocio_id": negocio_id,
            "total_evaluaciones": len(evaluaciones),
            "empleados_totales": negocio.empleados_directos + negocio.empleados_indirectos,
            "ingresos_mensuales": negocio.ingresos_mensuales_promedio,
            "antiguedad_meses": negocio.meses_operacion,
            "categoria_riesgo_actual": evaluaciones[-1].categoria_riesgo if evaluaciones else None,
            "deuda_total": negocio.deuda_existente,
            "ratio_deuda_ingresos": negocio.ratio_deuda_ingresos
        }

    def get_metricas_financieras(self, db: Session, negocio_id: int) -> Dict[str, Any]:
        negocio = self.get(db, negocio_id)
        if not negocio:
            raise ValueError("Negocio no encontrado")

        margen_utilidad = 0.0
        if negocio.ingresos_anuales > 0:
            margen_utilidad = (float(negocio.ingresos_anuales - negocio.deuda_existente) / float(negocio.ingresos_anuales)) * 100

        ratio_endeudamiento = 0.0
        if negocio.activos_totales > 0:
            ratio_endeudamiento = float(negocio.pasivos_totales) / float(negocio.activos_totales)

        liquidez_corriente = 0.0
        if negocio.pasivos_totales > 0:
            # Asumiendo que activos corrientes son el 60% de activos totales (simplificación)
            activos_corrientes = float(negocio.activos_totales) * 0.6
            liquidez_corriente = activos_corrientes / float(negocio.pasivos_totales)

        # Determinar salud financiera
        if ratio_endeudamiento < 0.3 and margen_utilidad > 20:
            salud_financiera = "EXCELENTE"
        elif ratio_endeudamiento < 0.5 and margen_utilidad > 10:
            salud_financiera = "BUENA"
        elif ratio_endeudamiento < 0.7 and margen_utilidad > 5:
            salud_financiera = "REGULAR"
        else:
            salud_financiera = "CRITICA"

        return {
            "negocio_id": negocio_id,
            "ratio_deuda_ingresos": float(negocio.ratio_deuda_ingresos) if negocio.ratio_deuda_ingresos else 0.0,
            "rentabilidad_estimada": float(negocio.rentabilidad_estimada) if negocio.rentabilidad_estimada else 0.0,
            "margen_utilidad": margen_utilidad,
            "ratio_endeudamiento": ratio_endeudamiento,
            "liquidez_corriente": liquidez_corriente,
            "salud_financiera": salud_financiera
        }

    def contar_por_sector(self, db: Session) -> Dict[str, int]:
        resultados = db.query(
            Negocio.sector_negocio,
            func.count(Negocio.id).label('total')
        ).group_by(Negocio.sector_negocio).all()
        
        return {resultado.sector_negocio: resultado.total for resultado in resultados}

negocio_repository = NegocioRepository()