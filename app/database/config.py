# config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cambio: importar Base desde models en lugar de crear una nueva
from .models import Base

load_dotenv()

# Configuración: credenciales PostgreSQL
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "girardot_db2025")

# URL de conexión con PostgreSQL usando psycopg2
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creación del motor
engine = create_engine(DATABASE_URL, echo=True)

# Sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ya no definimos Base aquí, la importamos de models

print(f"Intentando conectar a la base de datos: {DB_NAME} en {DB_HOST}")
try:
    # Esto verifica la conexión y crea las tablas si no existen.
    Base.metadata.create_all(bind=engine)
    print("✅ Las tablas de la base de datos se han creado o ya existían.")
except Exception as e:
    print(f" Error al crear las tablas de la base de datos: {e}")

# Dependencia para inyección de sesión en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()