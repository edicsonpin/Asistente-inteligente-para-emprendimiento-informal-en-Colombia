# core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Any
import secrets
import string
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.config2 import get_db



# Configuración de seguridad
SECRET_KEY = "tu-clave-secreta-super-segura-aqui-cambiar-en-produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    """Generar hash de contraseña usando bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar si una contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT de acceso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT de refresh"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# === FUNCIONES ESPECÍFICAS PARA FASTAPI ===
def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    """
    Verificar token para dependencias de FastAPI
    """
    # IMPORTAR DENTRO DE LA FUNCIÓN para evitar circular
    from repositories.usuarios import usuario_repository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = usuario_repository.get_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user
''''
async def get_current_user(
    token: str = Depends(security), 
    db: Session = Depends(get_db)
):
    """Obtener usuario actual desde el token"""
    return verify_token_dependency(token, db)
'''

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener usuario actual desde el token JWT
    Esta es la función que se usa como dependencia en los endpoints
    """
    # 💡 FIX: Importar DENTRO de la función para evitar el NameError
    from repositories.usuarios import usuario_repository # <-- ¡AÑADIR ESTA LÍNEA!

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extraer el token
        token = credentials.credentials
        
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Obtener usuario de la base de datos (Ahora usuario_repository está definido)
    user = usuario_repository.get_by_username(db, username=username)
    
    if user is None:
        raise credentials_exception
    
    return user









'''
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return verify_token_dependency(credentials, db)
'''
async def get_current_active_user(current_user = Depends(get_current_user)):
    """Verificar que el usuario esté activo"""
    if current_user.estado != "ACTIVO":
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

# === FUNCIONES DE UTILIDAD ===
def generate_password(length: int = 12) -> str:
    """Generar contraseña aleatoria segura"""
    if length < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    
    # Garantizar al menos un carácter de cada tipo
    uppercase = secrets.choice(string.ascii_uppercase)
    lowercase = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    
    # Resto de caracteres aleatorios
    remaining = length - 4
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    random_chars = ''.join(secrets.choice(all_chars) for _ in range(remaining))
    
    # Mezclar todos los caracteres
    password_chars = list(uppercase + lowercase + digit + special + random_chars)
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)

def validate_password_strength(password: str) -> dict:
    """Validar fortaleza de contraseña"""
    result = {
        "is_valid": True,
        "score": 0,
        "feedback": []
    }
    
    # Longitud mínima
    if len(password) < 8:
        result["is_valid"] = False
        result["feedback"].append("La contraseña debe tener al menos 8 caracteres")
    else:
        result["score"] += 1
    
    # Mayúsculas
    if any(c.isupper() for c in password):
        result["score"] += 1
    else:
        result["feedback"].append("Incluir al menos una letra mayúscula")
    
    # Minúsculas
    if any(c.islower() for c in password):
        result["score"] += 1
    else:
        result["feedback"].append("Incluir al menos una letra minúscula")
    
    # Dígitos
    if any(c.isdigit() for c in password):
        result["score"] += 1
    else:
        result["feedback"].append("Incluir al menos un número")
    
    # Caracteres especiales
    if any(not c.isalnum() for c in password):
        result["score"] += 1
    else:
        result["feedback"].append("Incluir al menos un carácter especial")
    
    return result

'''
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener usuario actual desde el token JWT
    Esta es la función que se usa como dependencia en los endpoints
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extraer el token
        token = credentials.credentials
        
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Obtener usuario de la base de datos
    user = usuario_repository.get_by_username(db, username=username)
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Verificar que el usuario esté activo
    """
    if current_user.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

'''

def generate_secure_token(length: int = 32) -> str:
    """Generar token seguro para URLs"""
    return secrets.token_urlsafe(length)

def get_token_data(token: str) -> Optional[dict]:
    """Obtener datos del token sin verificar expiración"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        return payload
    except JWTError:
        return None

def is_token_expired(token: str) -> bool:
    """Verificar si un token ha expirado"""
    payload = get_token_data(token)
    if not payload:
        return True
    
    exp_timestamp = payload.get("exp")
    if not exp_timestamp:
        return True
    
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    return datetime.utcnow() > exp_datetime