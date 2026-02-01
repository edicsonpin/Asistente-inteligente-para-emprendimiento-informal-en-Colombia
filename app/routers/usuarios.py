# routers/usuarios.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.config2 import get_db
from services.usuario_service import usuario_service
from schemas.usuarios import (
    UsuarioCreate, 
    UsuarioUpdate, 
    UsuarioInDB,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioFilter,
    PaginationParams
)
# ✅ CORREGIR: Cambiar de security.auth a core.security
from core.security import get_current_active_user

router = APIRouter()

@router.get("/usuarios/", response_model=UsuarioListResponse)
async def listar_usuarios(
    filtros: UsuarioFilter = Depends(),
    paginacion: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Obtener lista de usuarios con filtros y paginación
    """
    try:
        # En una implementación real, pasarías los filtros al servicio
        usuarios = usuario_service.get_usuarios(
            db, 
            skip=(paginacion.pagina - 1) * paginacion.por_pagina, 
            limit=paginacion.por_pagina
        )
        
        # Obtener total para paginación (en una implementación real)
        total_usuarios = len(usuarios)  # Esto sería una consulta COUNT en la BD
        
        return UsuarioListResponse(
            success=True,
            data=usuarios,
            total=total_usuarios,
            pagina=paginacion.pagina,
            por_pagina=paginacion.por_pagina
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(e)}"
        )

@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Obtener un usuario específico por ID
    """
    try:
        usuario = usuario_service.get_usuario(db, usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return UsuarioResponse(
            success=True,
            data=usuario,
            message="Usuario encontrado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )

@router.post("/usuarios/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Crear un nuevo usuario
    """
    try:
        # Verificar si el usuario actual tiene permisos para crear usuarios
        if current_user.tipo_usuario not in ["ADMINISTRADOR", "INSTITUCION"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para crear usuarios"
            )
        
        nuevo_usuario = usuario_service.create_usuario(db, usuario)
        
        return UsuarioResponse(
            success=True,
            data=nuevo_usuario,
            message="Usuario creado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Actualizar un usuario existente
    """
    try:
        # Verificar permisos: solo administradores o el propio usuario pueden actualizar
        if current_user.tipo_usuario != "ADMINISTRADOR" and current_user.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede actualizar su propio perfil"
            )
        
        usuario_actualizado = usuario_service.update_usuario(db, usuario_id, usuario)
        
        return UsuarioResponse(
            success=True,
            data=usuario_actualizado,
            message="Usuario actualizado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )

@router.delete("/usuarios/{usuario_id}")
async def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Eliminar un usuario (solo administradores)
    """
    try:
        # Solo administradores pueden eliminar usuarios
        if current_user.tipo_usuario != "ADMINISTRADOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden eliminar usuarios"
            )
        
        # No permitir auto-eliminación
        if current_user.usuario_id == usuario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede eliminarse a sí mismo"
            )
        
        usuario_service.delete_usuario(db, usuario_id)
        
        return {
            "success": True, 
            "message": "Usuario eliminado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}"
        )

@router.get("/usuarios/me/", response_model=UsuarioResponse)
async def obtener_usuario_actual(
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Obtener información del usuario actualmente autenticado
    """
    return UsuarioResponse(
        success=True,
        data=current_user,
        message="Información del usuario actual"
    )

@router.put("/usuarios/me/", response_model=UsuarioResponse)
async def actualizar_usuario_actual(
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_active_user)
):
    """
    Actualizar información del usuario actual
    """
    try:
        usuario_actualizado = usuario_service.update_usuario(db, current_user.usuario_id, usuario)
        
        return UsuarioResponse(
            success=True,
            data=usuario_actualizado,
            message="Perfil actualizado exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )