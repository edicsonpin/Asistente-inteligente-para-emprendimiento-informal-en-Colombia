from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import os

# ✅ SOLUCIÓN: Importar directamente desde database.py o database/__init__.py
try:
    from app.database1 import engine, Base, get_db
    print('entro a las tablas =================================================== ')
except ImportError:
    # Si falla, crear las variables directamente aquí temporalmente
    print('entro a las tablas ******************************************************** ')
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./proyecto_ai.db")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base = declarative_base()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

# ✅ Importar modelos (asegurarse de que están registrados en Base)
try:
    # Si tienes la estructura modular
    from app.database.models import *
    from app.database.models_mlops import *
    from app.database.models_xai import *
    from app.database.models_synthetic import *
    print(" MODELO IMPORTADOS EXITOSAMENTE++++++++++++++++++++++++++++++$$$$$$$$$$$$$$$$$$")
except ImportError:
    # Si no, definir algunos modelos básicos aquí temporalmente
    from sqlalchemy import Column, Integer, String
    class Usuario(Base):
        __tablename__ = "usuarios"
        usuario_id = Column(Integer, primary_key=True, index=True)
        username = Column(String(100), unique=True, nullable=False)
        email = Column(String(255), unique=True, nullable=False)

# ✅ Importar routers
from app.routers.usuarios import router as usuarios_router
from app.routers.roles import router as roles_router
try:
    from app.routers.usuarios import router as usuarios_router
    from app.routers.roles import router as roles_router
   # from app.routes.auth import router as auth_router
    print(" rutas cEXITOSAMENTE++++++++++++++++++++++++++++++$$$$$$$$$$$$$$$$$$")
except ImportError:
    print(" no rutas cEXITOSAMENTE++++++++++++++++++++++++++++++$$$$$$$$$$$$$$$$$$")
    # Crear routers básicos si no existen
    from fastapi import APIRouter
    usuarios_router = APIRouter()
    roles_router = APIRouter()
    auth_router = APIRouter()
    
    @usuarios_router.get("/")
    def listar_usuarios():
        return {"message": "Endpoint de usuarios - por implementar"}
    
    @roles_router.get("/")
    def listar_roles():
        return {"message": "Endpoint de roles - por implementar"}
    
    @auth_router.post("/login")
    def login():
        return {"message": "Login endpoint - por implementar"}

# Inicializar FastAPI
app = FastAPI(
    title="Proyecto AI Girardot",
    description="API para gestión de emprendedores 2025, oportunidades y recomendaciones con IA",
    version="1.0.0"
)

# Configurar CORS
print("esta funcionado++++++++++++++++++++++++++++++++++++++++++")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas al iniciar
@app.on_event("startup")
def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")

# Incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(usuarios_router, prefix="/api/usuarios", tags=["usuarios"])
app.include_router(roles_router, prefix="/api/roles", tags=["roles"])

# Rutas básicas
@app.get("/")
def read_root():
    return {"mensaje": "API Proyecto AI Girardot"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "SQLite"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)