# app/crud.py

from sqlalchemy.orm import Session
from . import models, schemas

# ------------------------
# CRUD GENERALES
# ------------------------

# Sector
def create_sector(db: Session, nombre: str):
    sector = models.Sector(nombre=nombre)
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return sector

def get_sector(db: Session, sector_id: int):
    return db.query(models.Sector).filter(models.Sector.sector_id == sector_id).first()

def get_sectores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sector).offset(skip).limit(limit).all()

def update_sector(db: Session, sector_id: int, nombre: str):
    sector = get_sector(db, sector_id)
    if sector:
        sector.nombre = nombre
        db.commit()
        db.refresh(sector)
    return sector

def delete_sector(db: Session, sector_id: int):
    sector = get_sector(db, sector_id)
    if sector:
        db.delete(sector)
        db.commit()
    return sector


# Institucion
def create_institucion(db: Session, nombre: str, tipo: str, nit: str):
    institucion = models.Institucion(nombre=nombre, tipo=tipo, nit=nit)
    db.add(institucion)
    db.commit()
    db.refresh(institucion)
    return institucion

def get_institucion(db: Session, institucion_id: int):
    return db.query(models.Institucion).filter(models.Institucion.institucion_id == institucion_id).first()

def get_instituciones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Institucion).offset(skip).limit(limit).all()


# Ciudad
def create_ciudad(db: Session, nombre: str):
    ciudad = models.Ciudad(nombre=nombre)
    db.add(ciudad)
    db.commit()
    db.refresh(ciudad)
    return ciudad

def get_ciudad(db: Session, ciudad_id: int):
    return db.query(models.Ciudad).filter(models.Ciudad.ciudad_id == ciudad_id).first()

def get_ciudades(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ciudad).offset(skip).limit(limit).all()


# Barrio
def create_barrio(db: Session, ciudad_id: int, nombre: str):
    barrio = models.Barrio(ciudad_id=ciudad_id, nombre=nombre)
    db.add(barrio)
    db.commit()
    db.refresh(barrio)
    return barrio

def get_barrio(db: Session, barrio_id: int):
    return db.query(models.Barrio).filter(models.Barrio.barrio_id == barrio_id).first()


# Emprendedor
def create_emprendedor(db: Session, nombre: str, telefono: str, email: str, nivel_digital: str):
    emprendedor = models.Emprendedor(nombre=nombre, telefono=telefono, email=email, nivel_digital=nivel_digital)
    db.add(emprendedor)
    db.commit()
    db.refresh(emprendedor)
    return emprendedor

def get_emprendedor(db: Session, emprendedor_id: int):
    return db.query(models.Emprendedor).filter(models.Emprendedor.emprendedor_id == emprendedor_id).first()


# Negocio
def create_negocio(db: Session, emprendedor_id: int, sector_id: int, formalidad: str, ventas_promedio: float, antiguedad_meses: int, barrio_id: int):
    negocio = models.Negocio(
        emprendedor_id=emprendedor_id,
        sector_id=sector_id,
        formalidad=formalidad,
        ventas_promedio=ventas_promedio,
        antiguedad_meses=antiguedad_meses,
        barrio_id=barrio_id
    )
    db.add(negocio)
    db.commit()
    db.refresh(negocio)
    return negocio

def get_negocio(db: Session, negocio_id: int):
    return db.query(models.Negocio).filter(models.Negocio.negocio_id == negocio_id).first()


# Oportunidad
def create_oportunidad(db: Session, institucion_id: int, tipo: str, nombre: str, requisitos: str, ciudad_destino: str, condiciones: dict, elegibilidad: dict):
    oportunidad = models.Oportunidad(
        institucion_id=institucion_id,
        tipo=tipo,
        nombre=nombre,
        requisitos=requisitos,
        ciudad_destino=ciudad_destino,
        condiciones=condiciones,
        elegibilidad=elegibilidad
    )
    db.add(oportunidad)
    db.commit()
    db.refresh(oportunidad)
    return oportunidad

def get_oportunidad(db: Session, oportunidad_id: int):
    return db.query(models.Oportunidad).filter(models.Oportunidad.oportunidad_id == oportunidad_id).first()


# Solicitud
def create_solicitud(db: Session, emprendedor_id: int, oportunidad_id: int, estado: str, monto_solicitado: float, monto_otorgado: float):
    solicitud = models.Solicitud(
        emprendedor_id=emprendedor_id,
        oportunidad_id=oportunidad_id,
        estado=estado,
        monto_solicitado=monto_solicitado,
        monto_otorgado=monto_otorgado
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud


# EvaluacionRiesgo
def create_evaluacion_riesgo(db: Session, emprendedor_id: int, negocio_id: int, model_version: str, score: float, label: str, shap_top_features: dict, umbral_usado: float):
    evaluacion = models.EvaluacionRiesgo(
        emprendedor_id=emprendedor_id,
        negocio_id=negocio_id,
        model_version=model_version,
        score=score,
        label=label,
        shap_top_features=shap_top_features,
        umbral_usado=umbral_usado
    )
    db.add(evaluacion)
    db.commit()
    db.refresh(evaluacion)
    return evaluacion


# Recomendacion
def create_recomendacion(db: Session, emprendedor_id: int, oportunidad_id: int, algoritmo: str, score: float, rank: int, fue_aceptada: bool):
    recomendacion = models.Recomendacion(
        emprendedor_id=emprendedor_id,
        oportunidad_id=oportunidad_id,
        algoritmo=algoritmo,
        score=score,
        rank=rank,
        fue_aceptada=fue_aceptada
    )
    db.add(recomendacion)
    db.commit()
    db.refresh(recomendacion)
    return recomendacion


# InteraccionAsistente
def create_interaccion(db: Session, emprendedor_id: int, canal: str, intencion: str, payload: dict):
    interaccion = models.InteraccionAsistente(
        emprendedor_id=emprendedor_id,
        canal=canal,
        intencion=intencion,
        payload=payload
    )
    db.add(interaccion)
    db.commit()
    db.refresh(interaccion)
    return interaccion


# Feedback
def create_feedback(db: Session, emprendedor_id: int, oportunidad_id: int, rating: int, comentario: str):
    feedback = models.Feedback(
        emprendedor_id=emprendedor_id,
        oportunidad_id=oportunidad_id,
        rating=rating,
        comentario=comentario
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


