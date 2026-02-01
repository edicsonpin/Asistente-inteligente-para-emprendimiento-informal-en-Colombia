# schemas/__init__.py

# Importa los esquemas que quieres exportar, pero sin causar circularidad.
# Si hay circularidad, usa imports diferidos.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .usuarios import UsuarioCreate, UsuarioUpdate, UsuarioInDB
    from .emprendedores import EmprendedorCreate, EmprendedorUpdate, EmprendedorInDB

# Luego, para que estén disponibles al importar desde schemas, puedes usar __all__
__all__ = [
    'UsuarioCreate', 'UsuarioUpdate', 'UsuarioInDB',
    'EmprendedorCreate', 'EmprendedorUpdate', 'EmprendedorInDB'
]