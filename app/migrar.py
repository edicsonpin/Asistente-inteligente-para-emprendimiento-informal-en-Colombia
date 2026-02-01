import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models import Pais, Departamento, Ciudad, Base
from app.database1 import engine

# ==============================
# 1️⃣ Crear sesión
# ==============================
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# ==============================
# 2️⃣ Crear tablas si no existen
# ==============================
Base.metadata.create_all(bind=engine)

# ==============================
# 3️⃣ Cargar archivo JSON
# ==============================
with open("countries+states+cities.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# ==============================
# 4️⃣ Insertar datos en la BD
# ==============================
for country in data:
    try:
        # Crear país
        pais_obj = Pais(
            nombre=country.get("name"),
            codigo_iso=country.get("iso3"),
            bandera_url=country.get("flag_url")
            
        )
        print(country.get("name")," .......................................................................")
        db.add(pais_obj)
        db.flush()  # Asigna el ID sin hacer commit aún

        
    except Exception as e:
        db.rollback()
        print(f"❌ Error importando {country.get('name')}: {e}")

# ==============================
# 5️⃣ Cerrar sesión
# ==============================
db.close()
