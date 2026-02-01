# routers/emprendedores.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.config2 import get_db
from schemas.emprendedores import EmprendedorCreate, EmprendedorUpdate, EmprendedorInDB
from repositories.emprendedores import emprendedor_repository
from core.security import get_current_active_user

router = APIRouter()

@router.post("/emprendedores/", response_model=EmprendedorInDB, status_code=status.HTTP_201_CREATED)
def crear_emprendedor(
    emprendedor: EmprendedorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        return emprendedor_repository.create(db, obj_in=emprendedor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/emprendedores/", response_model=List[EmprendedorInDB])
def listar_emprendedores(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if estado:
        return emprendedor_repository.buscar_por_estado(db, estado, skip, limit)
    return emprendedor_repository.get_multi(db, skip=skip, limit=limit)

@router.get("/emprendedores/{emprendedor_id}", response_model=EmprendedorInDB)
def obtener_emprendedor(
    emprendedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    emprendedor = emprendedor_repository.get(db, emprendedor_id)
    if not emprendedor:
        raise HTTPException(status_code=404, detail="Emprendedor no encontrado")
    return emprendedor

@router.get("/usuarios/{usuario_id}/emprendedor", response_model=EmprendedorInDB)
def obtener_emprendedor_por_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    emprendedor = emprendedor_repository.get_by_usuario(db, usuario_id)
    if not emprendedor:
        raise HTTPException(status_code=404, detail="Emprendedor no encontrado para este usuario")
    return emprendedor

@router.put("/emprendedores/{emprendedor_id}", response_model=EmprendedorInDB)
def actualizar_emprendedor(
    emprendedor_id: int,
    emprendedor: EmprendedorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_emprendedor = emprendedor_repository.get(db, emprendedor_id)
    if not db_emprendedor:
        raise HTTPException(status_code=404, detail="Emprendedor no encontrado")
    
    try:
        return emprendedor_repository.update(db, db_obj=db_emprendedor, obj_in=emprendedor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/emprendedores/{emprendedor_id}/estadisticas")
def obtener_estadisticas_emprendedor(
    emprendedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        return emprendedor_repository.get_estadisticas(db, emprendedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/emprendedores/{emprendedor_id}/actualizar-score")
def actualizar_score_completitud(
    emprendedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        emprendedor = emprendedor_repository.actualizar_score_completitud(db, emprendedor_id)
        return {"score_actualizado": emprendedor.score_completitud}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))