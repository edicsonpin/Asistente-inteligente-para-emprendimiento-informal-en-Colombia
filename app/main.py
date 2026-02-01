# main.py - Solo cambiar esta parte

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from sqlalchemy.orm import Session # Si no está importado, debe hacerlo
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from pathlib import Path
from app.database.models import *
from app.database.models_mlops import *
from app.database.models_xai import *
from app.database.models_synthetic import *


current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.database.config import  Base, get_db,DATABASE_URL
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Cambiar a False en producción
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
Base.metadata.create_all(bind=engine)
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
'''
from routers import (
    auth, usuarios, emprendedores, negocios, 
    evaluaciones, oportunidades, recomendaciones, xai, mlops
)
'''
from routers import (
    auth, usuarios,emprendedores, negocios,roles
)
# CAMBIAR: Usar get_current_user en lugar de verify_token
from core.security import get_current_user

# El resto del código permanece igual...


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación FastAPI...")
    yield
    print("Cerrando aplicación...")

app = FastAPI(
    title="Sistema de Recomendación para Emprendimiento Informal",
    description="API para el sistema de recomendación híbrido con XAI",
    version="2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

#  CAMBIAR: Usar get_current_user directamente
#async def get_current_user_dependency(token: str = Depends(security)):
 #   return await get_current_user(token)

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security), # Resuelve credenciales
    db: Session = Depends(get_db)                                # Resuelve la sesión de DB
):
    # Ahora, pasa AMBOS argumentos resueltos a la función de seguridad
    return await get_current_user(credentials=credentials, db=db)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1", tags=["Autenticación"])

# Incluir routers principales
app.include_router(auth.router, prefix="/api/v1", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/api/v1", tags=["Usuarios"])
#app.include_router(usuarios.router, prefix="/api/v1", tags=["Usuarios"], dependencies=[Depends(get_current_user_dependency)])

# Incluir routers que hemos creado
app.include_router(roles.router, prefix="/api/v1", tags=["Roles y Permisos"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(emprendedores.router, prefix="/api/v1", tags=["Emprendedores"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(negocios.router, prefix="/api/v1", tags=["Negocios"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(usuarios.router, prefix="/api/v1", tags=["Usuarios"], dependencies=[Depends(get_current_user_dependency)])
'''app.include_router(emprendedores.router, prefix="/api/v1", tags=["Emprendedores"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(negocios.router, prefix="/api/v1", tags=["Negocios"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(evaluaciones.router, prefix="/api/v1", tags=["Evaluaciones"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(oportunidades.router, prefix="/api/v1", tags=["Oportunidades"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(recomendaciones.router, prefix="/api/v1", tags=["Recomendaciones"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(xai.router, prefix="/api/v1", tags=["XAI"], dependencies=[Depends(get_current_user_dependency)])
app.include_router(mlops.router, prefix="/api/v1", tags=["MLOps"], dependencies=[Depends(get_current_user_dependency)])
'''
@app.get("/")
async def root():
    return {"message": "Sistema de Recomendación para Emprendimiento Informal - API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0"}




if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

'''
http://127.0.0.1:8000/api/v1/login


{
  "username": "edicsonpin",
  "password": "Elduro2019$"
}
'''

