from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuración: credenciales PostgreSQL (usar variables de entorno en producción)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "girardot_db22")

# URL de conexión con PostgreSQL usando psycopg2
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Conectando a la base de datos: {DB_HOST}:{DB_PORT}/{DB_NAME}")

# Creación del motor
engine = create_engine(
    DATABASE_URL, 
    echo=True,  # Cambiar a False en producción
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Sesión
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Base para modelos ORM
Base = declarative_base()

def get_db():
    """
    Dependencia para inyección de sesión en FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Crear todas las tablas en la base de datos
    """
    from . import models
    from . import models_xai
    from . import models_synthetic  
    from . import models_mlops
    
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente!")

def drop_tables():
    """
    Eliminar todas las tablas (solo para desarrollo)
    """
    Base.metadata.drop_all(bind=engine)
    print("Todas las tablas eliminadas!")

# Crear tablas al importar el módulo (solo en desarrollo)
if os.getenv("ENVIRONMENT") != "production":
    try:
        create_tables()
    except Exception as e:
        print(f"Error al crear tablas: {e}")