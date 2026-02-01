from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.roles import (
    RolCreate, RolUpdate, RolResponse, RolWithPermisos, RolWithUsuarios,
    RolSingleResponse, RolesListResponse, RolWithPermisosResponse, 
    RolWithUsuariosResponse, PermisoCreate, PermisoUpdate, 
    PermisoSingleResponse, PermisosListResponse
)
from app.services.roles import rol_service

router = APIRouter(prefix="/roles", tags=["roles"])

# Endpoints para Roles
@router.post("/", response_model=RolSingleResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(rol: RolCreate, db: Session = Depends(get_db)):
    """Crear un nuevo rol"""
    try:
        rol_creado = rol_service.create_rol(db, rol)
        return RolSingleResponse(
            success=True,
            message="Rol creado exitosamente",
            data=rol_creado
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=RolesListResponse)
def listar_roles(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    activos: bool = Query(True, description="Filtrar solo roles activos"),
    nivel_minimo: Optional[int] = Query(None, ge=0, description="Nivel de permiso mínimo"),
    nivel_maximo: Optional[int] = Query(None, ge=0, description="Nivel de permiso máximo"),
    db: Session = Depends(get_db)
):
    """Listar todos los roles con paginación y filtros"""
    if nivel_minimo is not None:
        roles = rol_service.get_roles_by_nivel_permiso(db, nivel_minimo, nivel_maximo)
    elif activos:
        roles = rol_service.get_roles_activos(db, skip=skip, limit=limit)
    else:
        roles = rol_service.get_roles(db, skip=skip, limit=limit)
    
    return RolesListResponse(
        success=True,
        message=f"Se encontraron {len(roles)} roles",
        data=roles
    )

@router.get("/{rol_id}", response_model=RolSingleResponse)
def obtener_rol(rol_id: int, db: Session = Depends(get_db)):
    """Obtener un rol por ID"""
    rol = rol_service.get_rol(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return RolSingleResponse(
        success=True,
        message="Rol encontrado",
        data=rol
    )

@router.get("/{rol_id}/permisos", response_model=RolWithPermisosResponse)
def obtener_rol_con_permisos(rol_id: int, db: Session = Depends(get_db)):
    """Obtener un rol con sus permisos"""
    rol = rol_service.get_rol_with_permisos(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return RolWithPermisosResponse(
        success=True,
        message="Rol con permisos encontrado",
        data=rol
    )

@router.get("/{rol_id}/usuarios", response_model=RolWithUsuariosResponse)
def obtener_rol_con_usuarios(rol_id: int, db: Session = Depends(get_db)):
    """Obtener un rol con sus usuarios"""
    rol = rol_service.get_rol_with_usuarios(db, rol_id)
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return RolWithUsuariosResponse(
        success=True,
        message=f"Rol con {rol.usuarios_count} usuarios encontrado",
        data=rol
    )

@router.put("/{rol_id}", response_model=RolSingleResponse)
def actualizar_rol(
    rol_id: int, 
    rol: RolUpdate, 
    db: Session = Depends(get_db)
):
    """Actualizar información de rol"""
    try:
        rol_actualizado = rol_service.update_rol(db, rol_id, rol)
        if not rol_actualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado"
            )
        return RolSingleResponse(
            success=True,
            message="Rol actualizado exitosamente",
            data=rol_actualizado
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{rol_id}/activar")
def activar_rol(rol_id: int, db: Session = Depends(get_db)):
    """Activar un rol"""
    success = rol_service.activar_rol(db, rol_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return {
        "success": True,
        "message": "Rol activado exitosamente"
    }

@router.put("/{rol_id}/desactivar")
def desactivar_rol(rol_id: int, db: Session = Depends(get_db)):
    """Desactivar un rol"""
    success = rol_service.desactivar_rol(db, rol_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return {
        "success": True,
        "message": "Rol desactivado exitosamente"
    }

@router.delete("/{rol_id}")
def eliminar_rol(rol_id: int, db: Session = Depends(get_db)):
    """Eliminar un rol"""
    try:
        success = rol_service.delete_rol(db, rol_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado"
            )
        return {
            "success": True,
            "message": "Rol eliminado exitosamente"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Endpoints para Permisos
@router.get("/{rol_id}/permisos-lista", response_model=PermisosListResponse)
def listar_permisos_del_rol(rol_id: int, db: Session = Depends(get_db)):
    """Listar todos los permisos de un rol"""
    permisos = rol_service.get_permisos_by_rol(db, rol_id)
    return PermisosListResponse(
        success=True,
        message=f"Se encontraron {len(permisos)} permisos",
        data=permisos
    )

@router.post("/{rol_id}/permisos", response_model=PermisoSingleResponse, status_code=status.HTTP_201_CREATED)
def agregar_permiso_a_rol(
    rol_id: int,
    permiso: PermisoCreate,
    db: Session = Depends(get_db)
):
    """Agregar un permiso a un rol"""
    try:
        permiso_creado = rol_service.add_permiso_to_rol(db, rol_id, permiso)
        return PermisoSingleResponse(
            success=True,
            message="Permiso agregado al rol exitosamenteeeee",
            data=permiso_creado
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/permisos/{permiso_id}", response_model=PermisoSingleResponse)
def obtener_permiso(permiso_id: int, db: Session = Depends(get_db)):
    """Obtener un permiso por ID"""
    permiso = rol_service.get_permiso(db, permiso_id)
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    return PermisoSingleResponse(
        success=True,
        message="Permiso encontrado",
        data=permiso
    )

@router.put("/permisos/{permiso_id}", response_model=PermisoSingleResponse)
def actualizar_permiso(
    permiso_id: int,
    permiso: PermisoUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar un permiso"""
    permiso_actualizado = rol_service.update_permiso(db, permiso_id, permiso)
    if not permiso_actualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    return PermisoSingleResponse(
        success=True,
        message="Permiso actualizado exitosamente",
        data=permiso_actualizado
    )

@router.delete("/permisos/{permiso_id}")
def eliminar_permiso(permiso_id: int, db: Session = Depends(get_db)):
    """Eliminar un permiso"""
    success = rol_service.remove_permiso_from_rol(db, permiso_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    return {
        "success": True,
        "message": "Permiso eliminado exitosamente"
    }

@router.get("/{rol_id}/verificar-permiso/{modulo}/{accion}")
def verificar_permiso(
    rol_id: int,
    modulo: str,
    accion: str,
    db: Session = Depends(get_db)
):
    """Verificar si un rol tiene un permiso específico"""
    tiene_permiso = rol_service.verificar_permiso(db, rol_id, modulo, accion)
    return {
        "success": True,
        "tiene_permiso": tiene_permiso,
        "modulo": modulo,
        "accion": accion,
        "rol_id": rol_id
    }