from fastapi import HTTPException, status

class NoEncontradoExcepcion(HTTPException):
    def __init__(self, detalle: str = "Recurso no encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detalle)

class NoAutorizadoExcepcion(HTTPException):
    def __init__(self, detalle: str = "No autorizado"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detalle)

class ProhibidoExcepcion(HTTPException):
    def __init__(self, detalle: str = "Prohibido"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detalle)

class SolicitudIncorrectaExcepcion(HTTPException):
    def __init__(self, detalle: str = "Solicitud incorrecta"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detalle)

class ModeloNoDisponibleExcepcion(HTTPException):
    def __init__(self, detalle: str = "Modelo ML no disponible"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detalle)