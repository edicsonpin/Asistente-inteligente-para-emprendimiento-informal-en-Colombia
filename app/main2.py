from fastapi import FastAPI
from app.database1 import engine, Base

# ✅ Importación modular y explícita

from app.database.models import *
from app.database.models_mlops import *
from app.database.models_xai import *
from app.database.models_synthetic import *

# Importamos los routers
from app import auth
from app.routers import roles1, usuarios1

app = FastAPI(
    title="Proyecto AI Girardot",
    description="API para gestión de emprendedores, oportunidades y recomendaciones con IA",
    version="1.0.0"
)

# Crear tablas - todas comparten el mismo Base
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Proyecto AI Girardot"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": str(engine.url)}

# Incluir routers
app.include_router(auth.router)
app.include_router(roles1.router)
app.include_router(usuarios1.router)