"""
Edicson Pineda Cadena -2025-
Modulo de configuracion central del sistema
Asistente Inteligente para Emprendimiento Informal en Colombia

Este modulo gestiona todas las variables de configuracion del sistema,
cargadas desde variables de entorno o archivo .env
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os
from pathlib import Path


class Configuracion(BaseSettings):
    """
    Clase de configuracion principal del sistema
    Utiliza Pydantic para validacion automatica de tipos
    """
    
    # ============================================
    # CONFIGURACION DE BASE DE DATOS
    # ============================================
    
    URL_BASE_DATOS: str
    """URL de conexion a PostgreSQL"""
    
    POOL_SIZE_BD: int = 20
    """Tamaño del pool de conexiones a base de datos"""
    
    MAX_OVERFLOW_BD: int = 10
    """Conexiones adicionales permitidas sobre el pool base"""
    
    POOL_RECYCLE_BD: int = 3600
    """Tiempo en segundos para reciclar conexiones (default: 1 hora)"""
    
    POOL_PRE_PING_BD: bool = True
    """Verificar conexion antes de usar del pool"""
    
    ECHO_SQL: bool = False
    """Mostrar SQL generado en logs (solo para debug)"""
    
    # ============================================
    # CONFIGURACION DE REDIS (CACHE)
    # ============================================
    
    URL_REDIS: str
    """URL de conexion a Redis para cache"""
    
    TIEMPO_EXPIRACION_CACHE: int = 300
    """Tiempo de expiracion por defecto del cache en segundos (5 minutos)"""
    
    MAX_CONEXIONES_REDIS: int = 50
    """Maximo de conexiones al pool de Redis"""
    
    # ============================================
    # CONFIGURACION DE SEGURIDAD JWT
    # ============================================
    
    CLAVE_SECRETA_JWT: str
    """Clave secreta para firmar tokens JWT - DEBE SER SEGURA"""
    
    ALGORITMO_JWT: str = "HS256"
    """Algoritmo de encriptacion para JWT"""
    
    MINUTOS_EXPIRACION_TOKEN: int = 30
    """Tiempo de expiracion de tokens de acceso en minutos"""
    
    MINUTOS_EXPIRACION_REFRESH: int = 10080
    """Tiempo de expiracion de refresh tokens en minutos (7 dias)"""
    
    INTENTOS_MAXIMOS_LOGIN: int = 5
    """Intentos maximos de login antes de bloquear cuenta"""
    
    # ============================================
    # CONFIGURACION DE API
    # ============================================
    
    RUTA_API_V1: str = "/api/v1"
    """Prefijo base para endpoints de API v1"""
    
    NOMBRE_PROYECTO: str = "Asistente Emprendedor"
    """Nombre del proyecto para documentacion"""
    
    VERSION_API: str = "1.0.0"
    """Version de la API"""
    
    DESCRIPCION_API: str = "Sistema de Recomendacion Hibrido con Explicabilidad para Emprendimiento Informal"
    """Descripcion del proyecto"""
    
    CONTACTO_API: dict = {
        "nombre": "Equipo de Desarrollo",
        "email": "soporte@asistente-emprendedor.co",
        "url": "https://asistente-emprendedor.co"
    }
    """Informacion de contacto para documentacion"""
    
    LICENCIA_API: dict = {
        "nombre": "Trabajo Fin de Master (TFM)",
        "url": "https://asistente-emprendedor.co/licencia"
    }
    """Informacion de licencia"""
    
    # ============================================
    # CONFIGURACION DE CORS
    # ============================================
    
    ORIGENES_CORS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:8080"
    ]
    """Lista de origenes permitidos para CORS"""
    
    PERMITIR_CREDENCIALES_CORS: bool = True
    """Permitir envio de credenciales en requests CORS"""
    
    METODOS_PERMITIDOS_CORS: List[str] = ["*"]
    """Metodos HTTP permitidos para CORS"""
    
    HEADERS_PERMITIDOS_CORS: List[str] = ["*"]
    """Headers HTTP permitidos para CORS"""
    
    # ============================================
    # CONFIGURACION DE MLFLOW
    # ============================================
    
    URI_MLFLOW: Optional[str] = None
    """URI del servidor de tracking de MLflow"""
    
    EXPERIMENTO_MLFLOW: str = "asistente-emprendedor"
    """Nombre del experimento en MLflow"""
    
    RUTA_ARTEFACTOS_MLFLOW: str = "./mlflow_artifacts"
    """Ruta local para almacenar artefactos de MLflow"""
    
    # ============================================
    # CONFIGURACION DE MODELO ML
    # ============================================
    
    RUTA_MODELO_LIGHTGBM: str = "./modelos/lightgbm_model.txt"
    """Ruta al archivo del modelo LightGBM entrenado"""
    
    RUTA_MODELO_EMBEDDINGS: str = "./modelos/embedding_model.h5"
    """Ruta al modelo de embeddings de TensorFlow"""
    
    UMBRAL_CONFIANZA_MODELO: float = 0.7
    """Umbral minimo de confianza para aceptar predicciones"""
    
    DIMENSION_EMBEDDINGS: int = 128
    """Dimension de los vectores de embeddings"""
    
    CATEGORIAS_RIESGO: List[str] = ["MUY_BAJO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
    """Categorias de clasificacion de riesgo"""
    
    # ============================================
    # CONFIGURACION DE XAI (EXPLICABILIDAD)
    # ============================================
    
    ACTIVAR_SHAP: bool = True
    """Activar generacion de explicaciones SHAP"""
    
    ACTIVAR_LIME: bool = True
    """Activar generacion de explicaciones LIME"""
    
    ACTIVAR_CONTRAFACTUALES: bool = True
    """Activar generacion de explicaciones contrafactuales"""
    
    NUM_CARACTERISTICAS_PRINCIPALES: int = 5
    """Numero de caracteristicas principales a mostrar en explicaciones"""
    
    # ============================================
    # CONFIGURACION DE DATOS SINTETICOS
    # ============================================
    
    ACTIVAR_DATOS_SINTETICOS: bool = True
    """Permitir uso de datos sinteticos para balanceo"""
    
    PORCENTAJE_DATOS_SINTETICOS: float = 0.3
    """Porcentaje de datos sinteticos en dataset (30%)"""
    
    UMBRAL_CALIDAD_SINTETICOS: float = 0.85
    """Umbral minimo de calidad para aceptar datos sinteticos"""
    
    # ============================================
    # CONFIGURACION DE MONITOREO
    # ============================================
    
    ACTIVAR_MONITOREO: bool = True
    """Activar monitoreo de modelo en produccion"""
    
    UMBRAL_DRIFT_DATOS: float = 0.15
    """Umbral para detectar drift en datos (15%)"""
    
    UMBRAL_DRIFT_CONCEPTO: float = 0.15
    """Umbral para detectar drift conceptual (15%)"""
    
    UMBRAL_DEGRADACION: float = 0.10
    """Umbral de degradacion de accuracy para alertar (10%)"""
    
    FRECUENCIA_MONITOREO_MINUTOS: int = 60
    """Frecuencia de monitoreo en minutos"""
    
    # ============================================
    # CONFIGURACION DE EQUIDAD
    # ============================================
    
    UMBRAL_DISPARATE_IMPACT: float = 0.8
    """Umbral minimo de disparate impact (estandar UNESCO)"""
    
    UMBRAL_DIFERENCIA_FN: float = 0.05
    """Umbral maximo de diferencia en tasa de falsos negativos (5%)"""
    
    VARIABLES_PROTEGIDAS: List[str] = ["genero", "region", "edad", "nivel_educacion"]
    """Variables protegidas para analisis de equidad"""
    
    # ============================================
    # CONFIGURACION DE RENDIMIENTO
    # ============================================
    
    LATENCIA_MAXIMA_MS: int = 300
    """Latencia maxima aceptable para predicciones en milisegundos"""
    
    REQUESTS_POR_MINUTO: int = 100
    """Limite de requests por minuto por usuario"""
    
    TIMEOUT_REQUEST_SEGUNDOS: int = 30
    """Timeout para requests HTTP en segundos"""
    
    WORKERS_UVICORN: int = 4
    """Numero de workers de Uvicorn en produccion"""
    
    # ============================================
    # CONFIGURACION DE LOGGING
    # ============================================
    
    NIVEL_LOG: str = "INFO"
    """Nivel de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL"""
    
    RUTA_LOGS: str = "./logs"
    """Directorio para almacenar logs"""
    
    TAMAÑO_MAXIMO_LOG_MB: int = 10
    """Tamaño maximo de archivo de log en MB"""
    
    CANTIDAD_BACKUPS_LOG: int = 5
    """Cantidad de archivos de backup de logs a mantener"""
    
    FORMATO_LOG: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    """Formato de mensajes de log"""
    
    # ============================================
    # CONFIGURACION DE ARCHIVOS
    # ============================================
    
    RUTA_ARCHIVOS_SUBIDOS: str = "./archivos_subidos"
    """Directorio para archivos subidos por usuarios"""
    
    TAMAÑO_MAXIMO_ARCHIVO_MB: int = 10
    """Tamaño maximo de archivo permitido en MB"""
    
    EXTENSIONES_PERMITIDAS: List[str] = [".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".csv"]
    """Extensiones de archivo permitidas"""
    
    # ============================================
    # CONFIGURACION DE EMAIL (OPCIONAL)
    # ============================================
    
    SMTP_HOST: Optional[str] = None
    """Host del servidor SMTP para envio de emails"""
    
    SMTP_PORT: int = 587
    """Puerto del servidor SMTP"""
    
    SMTP_USUARIO: Optional[str] = None
    """Usuario para autenticacion SMTP"""
    
    SMTP_CONTRASENA: Optional[str] = None
    """Contrasena para autenticacion SMTP"""
    
    EMAIL_DESDE: Optional[str] = None
    """Email desde el cual enviar notificaciones"""
    
    ACTIVAR_NOTIFICACIONES_EMAIL: bool = False
    """Activar envio de notificaciones por email"""
    
    # ============================================
    # CONFIGURACION DE AMBIENTE
    # ============================================
    
    AMBIENTE: str = "desarrollo"
    """Ambiente de ejecucion: desarrollo, staging, produccion"""
    
    DEPURACION: bool = False
    """Modo debug activado (NO usar en produccion)"""
    
    MODO_PRUEBAS: bool = False
    """Modo de pruebas automatizadas"""
    
    # ============================================
    # CONFIGURACION DE BACKUP
    # ============================================
    
    ACTIVAR_BACKUP_AUTOMATICO: bool = True
    """Activar backups automaticos"""
    
    RUTA_BACKUPS: str = "/var/backups/asistente"
    """Directorio para almacenar backups"""
    
    DIAS_RETENCION_BACKUP: int = 30
    """Dias de retencion de backups"""
    
    HORA_BACKUP: str = "02:00"
    """Hora del dia para ejecutar backup automatico (formato 24h)"""
    
    # ============================================
    # CONFIGURACION AVANZADA
    # ============================================
    
    ACTIVAR_COMPRESION_GZIP: bool = True
    """Activar compresion gzip en responses"""
    
    TAMAÑO_MINIMO_COMPRESION_KB: int = 1
    """Tamaño minimo de response para comprimir (en KB)"""
    
    ACTIVAR_RATE_LIMITING: bool = True
    """Activar limitacion de tasa de requests"""
    
    ACTIVAR_METRICAS_PROMETHEUS: bool = True
    """Exponer metricas para Prometheus"""
    
    RUTA_METRICAS: str = "/metrics"
    """Endpoint para metricas de Prometheus"""
    
    # ============================================
    # CONFIGURACION DE DOCUMENTACION
    # ============================================
    
    RUTA_DOCS: str = "/documentacion"
    """Ruta para documentacion Swagger UI"""
    
    RUTA_REDOC: str = "/redoc"
    """Ruta para documentacion ReDoc"""
    
    ACTIVAR_DOCS: bool = True
    """Activar documentacion interactiva"""
    
    # ============================================
    # METODOS DE VALIDACION
    # ============================================
    
    @property
    def es_desarrollo(self) -> bool:
        """Verifica si esta en ambiente de desarrollo"""
        return self.AMBIENTE.lower() == "desarrollo"
    
    @property
    def es_produccion(self) -> bool:
        """Verifica si esta en ambiente de produccion"""
        return self.AMBIENTE.lower() == "produccion"
    
    @property
    def es_staging(self) -> bool:
        """Verifica si esta en ambiente de staging"""
        return self.AMBIENTE.lower() == "staging"
    
    def validar_configuracion(self) -> dict:
        """
        Valida la configuracion y retorna advertencias si hay problemas
        
        Returns:
            dict: Diccionario con advertencias y errores encontrados
        """
        advertencias = []
        errores = []
        
        # Validar clave JWT en produccion
        if self.es_produccion and len(self.CLAVE_SECRETA_JWT) < 32:
            errores.append("CLAVE_SECRETA_JWT debe tener al menos 32 caracteres en produccion")
        
        # Validar debug en produccion
        if self.es_produccion and self.DEPURACION:
            advertencias.append("DEPURACION activado en produccion - esto es un riesgo de seguridad")
        
        # Validar CORS
        if self.es_produccion and "*" in self.ORIGENES_CORS:
            advertencias.append("CORS permite todos los origenes (*) en produccion")
        
        # Validar pool de BD
        if self.POOL_SIZE_BD < 10:
            advertencias.append(f"POOL_SIZE_BD es muy bajo ({self.POOL_SIZE_BD}) - recomendado: 20+")
        
        # Validar latencia
        if self.LATENCIA_MAXIMA_MS > 500:
            advertencias.append(f"LATENCIA_MAXIMA_MS muy alta ({self.LATENCIA_MAXIMA_MS}ms)")
        
        return {
            "valido": len(errores) == 0,
            "errores": errores,
            "advertencias": advertencias
        }
    
    def obtener_info_ambiente(self) -> dict:
        """
        Obtiene informacion sobre el ambiente actual
        
        Returns:
            dict: Informacion del ambiente
        """
        return {
            "ambiente": self.AMBIENTE,
            "version_api": self.VERSION_API,
            "depuracion": self.DEPURACION,
            "modo_pruebas": self.MODO_PRUEBAS,
            "base_datos_configurada": bool(self.URL_BASE_DATOS),
            "redis_configurado": bool(self.URL_REDIS),
            "mlflow_configurado": bool(self.URI_MLFLOW),
            "email_configurado": bool(self.SMTP_HOST and self.SMTP_USUARIO),
            "documentacion_activa": self.ACTIVAR_DOCS,
            "monitoreo_activo": self.ACTIVAR_MONITOREO
        }
    
    # ============================================
    # CONFIGURACION DE PYDANTIC
    # ============================================
    
    class Config:
        """Configuracion de Pydantic BaseSettings"""
        
        env_file = ".env"
        """Archivo de donde cargar variables de entorno"""
        
        env_file_encoding = "utf-8"
        """Codificacion del archivo .env"""
        
        case_sensitive = True
        """Las variables de entorno son case-sensitive"""
        
        extra = "ignore"
        """Ignorar variables extra no definidas"""


@lru_cache()
def obtener_configuracion() -> Configuracion:
    """
    Obtiene instancia singleton de configuracion
    Usa cache para evitar recrear el objeto
    
    Returns:
        Configuracion: Instancia de configuracion del sistema
    """
    return Configuracion()


# Instancia global de configuracion
configuracion = obtener_configuracion()


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def mostrar_configuracion_segura() -> dict:
    """
    Muestra configuracion sin datos sensibles
    Util para debugging y logs
    
    Returns:
        dict: Configuracion sin datos sensibles
    """
    config_dict = configuracion.dict()
    
    # Campos sensibles a ocultar
    campos_sensibles = [
        "CLAVE_SECRETA_JWT",
        "URL_BASE_DATOS",
        "URL_REDIS",
        "SMTP_CONTRASENA",
        "SMTP_USUARIO"
    ]
    
    # Ocultar campos sensibles
    for campo in campos_sensibles:
        if campo in config_dict:
            config_dict[campo] = "***OCULTO***"
    
    return config_dict


def validar_configuracion_startup():
    """
    Valida la configuracion al iniciar la aplicacion
    Lanza excepcion si hay errores criticos
    """
    resultado = configuracion.validar_configuracion()
    
    if not resultado["valido"]:
        errores_texto = "\n".join(f"  - {error}" for error in resultado["errores"])
        raise ValueError(f"Errores en configuracion:\n{errores_texto}")
    
    if resultado["advertencias"]:
        import warnings
        for advertencia in resultado["advertencias"]:
            warnings.warn(f"Advertencia de configuracion: {advertencia}")


def crear_directorios_necesarios():
    """
    Crea directorios necesarios si no existen
    """
    directorios = [
        configuracion.RUTA_LOGS,
        configuracion.RUTA_ARCHIVOS_SUBIDOS,
        configuracion.RUTA_ARTEFACTOS_MLFLOW,
        configuracion.RUTA_BACKUPS
    ]
    
    for directorio in directorios:
        Path(directorio).mkdir(parents=True, exist_ok=True)


# ============================================
# INICIALIZACION AUTOMATICA
# ============================================

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar configuracion
    print("=== CONFIGURACION DEL SISTEMA ===\n")
    
    # Validar configuracion
    try:
        validar_configuracion_startup()
        print("✓ Configuracion valida\n")
    except ValueError as e:
        print(f"✗ Error en configuracion:\n{e}\n")
        exit(1)
    
    # Mostrar informacion del ambiente
    print("Informacion del ambiente:")
    info = configuracion.obtener_info_ambiente()
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")
    
    print("\nConfiguracion (sin datos sensibles):")
    config_segura = mostrar_configuracion_segura()
    for clave, valor in sorted(config_segura.items()):
        if not clave.startswith("_"):
            print(f"  {clave}: {valor}")
