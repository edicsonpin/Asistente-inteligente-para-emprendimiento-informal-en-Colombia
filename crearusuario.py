from database import SessionLocal
from database import Usuario
from core.security import hash_password

db = SessionLocal()

# Datos del usuario administrador inicial
email = "admin@mail.com"
password = "12345"

# Verificar si ya existe
existing = db.query(Usuario).filter(Usuario.email == email).first()
if existing:
    print("El usuario ya existe.")
else:
    nuevo = Usuario(
        email=email,
        password=hash_password(password),
        nombre="Administrador",
        rol_id=1  # Asegúrate que existe un rol 1 (Admin)
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    print("Usuario creado: ", nuevo.email)
