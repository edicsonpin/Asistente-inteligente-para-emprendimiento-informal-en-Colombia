
from passlib.context import CryptContext
from werkzeug.security import generate_password_hash, check_password_hash

# Contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña en texto plano coincide con la hasheada"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash seguro para la contraseña"""
    return pwd_context.hash(password) 