# routers/negocios.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.config2 import get_db
from schemas.negocios import NegocioCreate, NegocioUpdate, NegocioInDB
from repositories.negocios import negocio_repository
from core.security import get_current_active_user

router = APIRouter()

@router.post("/negocios/", response_model=NegocioInDB, status_code=status.HTTP_201_CREATED)
def crear_negocio(
    negocio: NegocioCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        return negocio_repository.create(db, obj_in=negocio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/negocios/", response_model=List[NegocioInDB])
def listar_negocios(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = Query(None),
    emprendedor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if sector:
        return negocio_repository.buscar_por_sector(db, sector, skip, limit)
    elif emprendedor_id:
        return negocio_repository.get_by_emprendedor(db, emprendedor_id)
    return negocio_repository.get_multi(db, skip=skip, limit=limit)

@router.get("/negocios/{negocio_id}", response_model=NegocioInDB)
def obtener_negocio(
    negocio_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    negocio = negocio_repository.get(db, negocio_id)
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return negocio

@router.get("/emprendedores/{emprendedor_id}/negocios", response_model=List[NegocioInDB])
def obtener_negocios_emprendedor(
    emprendedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return negocio_repository.get_by_emprendedor(db, emprendedor_id)

@router.put("/negocios/{negocio_id}", response_model=NegocioInDB)
def actualizar_negocio(
    negocio_id: int,
    negocio: NegocioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_negocio = negocio_repository.get(db, negocio_id)
    if not db_negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    try:
        return negocio_repository.update(db, db_obj=db_negocio, obj_in=negocio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/negocios/{negocio_id}/estadisticas")
def obtener_estadisticas_negocio(
    negocio_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        return negocio_repository.get_estadisticas_negocio(db, negocio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/negocios/{negocio_id}/metricas-financieras")
def obtener_metricas_financieras(
    negocio_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        return negocio_repository.get_metricas_financieras(db, negocio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/negocios/estadisticas/sectores")
def obtener_estadisticas_sectores(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return negocio_repository.contar_por_sector(db)