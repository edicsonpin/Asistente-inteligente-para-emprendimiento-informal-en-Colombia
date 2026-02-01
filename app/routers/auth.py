# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import Request, HTTPException

from app.database.config2 import get_db
from services.usuario_service import usuario_service
from schemas.usuarios import Token, LoginRequest, LoginResponse
# CORREGIR: Importar desde core.security en lugar de security.auth
from core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter()
async def read_login_input(request: Request):
    # 1. Intentar leer JSON
    try:
        data = await request.json()
        if "username" in data and "password" in data:
            return data["username"], data["password"]
    except:
        pass  # No es JSON

    # 2. Intentar leer form-data / x-www-form-urlencoded
    form = await request.form()
    if "username" in form and "password" in form:
        return form["username"], form["password"]

    # 3. Si no encuentra nada → error claro
    raise HTTPException(
        status_code=422,
        detail="Debe enviar username y password en JSON o x-www-form-urlencoded"
    )


@router.post("/login", response_model=LoginResponse)
async def login_unificado(request: Request, db: Session = Depends(get_db)):
    
    username, password = await read_login_input(request)

    user = usuario_service.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Actualizar último login
    usuario_service.repository.update_last_login(db, user.usuario_id)

    access_token = create_access_token(data={"sub": username})
    refresh_token = create_refresh_token(data={"sub": username})

    return LoginResponse(
        success=True,
        data=Token(
            access_token=access_token,
            token_type="bearer"
        ),
        user=user,
        message="Login exitoso"
    )


@router.post("/login-json", response_model=LoginResponse)
async def login_with_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login usando JSON en lugar de form-data
    """
    user = usuario_service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último login
    usuario_service.repository.update_last_login(db, user.usuario_id)
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        success=True,
        data=Token(access_token=access_token, token_type="bearer"),
        user=user,
        message="Login exitoso"
    )

@router.post("/refresh-token")
async def refresh_token_endpoint(refresh_token: str, db: Session = Depends(get_db)):
    """
    Obtener nuevo access token usando refresh token
    """
    # ✅ Ya estamos importando verify_token y create_access_token desde core.security
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    username = payload.get("sub")
    user = usuario_service.get_usuario_by_username(db, username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    new_access_token = create_access_token(data={"sub": username})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout():
    """
    Cerrar sesión
    """
    return {"message": "Logout exitoso"}