# app/crearusuario.py

from database.config2 import get_db
from database.models import Usuario, TipoUsuario, EstadoUsuario
from core.security import get_password_hash


def crear_usuario():
    db = next(get_db())

    usuario = Usuario(
        username="edicsonpin1",
        email="edics@gmail1.com",
        password_hash=get_password_hash("Elduro2019$"),
         tipo_usuario=TipoUsuario.ADMINISTRADOR,
        estado=EstadoUsuario.ACTIVO,
        nombre_completo="Edicson Pin"
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    print("Usuario creado con ID:", usuario.usuario_id)


if __name__ == "__main__":
    crear_usuario()

