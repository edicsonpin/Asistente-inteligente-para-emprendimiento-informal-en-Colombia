from fastapi import FastAPI
from app.database1 import engine, Base
#from app import models
from app.modelos import core_models
 # importa tu router
from app import auth, routers
from app.routers import roles1, usuarios1
#uvicorn app.main:app --reload
# Inicializamos la app FastAPI (solo una vez)
app = FastAPI(
    title="Proyecto AI Girardot",
    description="API para gestión de emprendedores, oportunidades y recomendaciones con IA",
    version="1.0.0"
)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Ruta raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido al Proyecto AI Girardot"}

# Healthcheck
@app.get("/health")
def health_check():
    return {"status": "ok", "database": str(engine.url)}
@app.get("/")
def root():
    return {"mensaje": "API Roles funcionando 🚀"}
# Incluir router de Emprendedor
#app.include_router(Emprendedor.router, prefix="/emprendedores", tags=["Emprendedores"])
#app.include_router(routes.Emprendedor.router)  
app.include_router(auth.router)
app.include_router(roles1.router)
app.include_router(usuarios1.router)