# database/models.py
'''
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, CheckConstraint, Enum as SQLEnum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import datetime

Base = declarative_base()

# ===============================
# Tablas de Asociación
# ===============================
usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.usuario_id"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("roles.rol_id"), primary_key=True)
)

# ===============================
# Enums
# ===============================

class TipoUsuario(str, enum.Enum):
    EMPRENDEDOR = "EMPRENDEDOR"
    INSTITUCION = "INSTITUCION"
    ADMINISTRADOR = "ADMINISTRADOR"
    CONSULTOR = "CONSULTOR"
    ANALISTA = "ANALISTA"

class EstadoUsuario(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    PENDIENTE = "PENDIENTE"
    BLOQUEADO = "BLOQUEADO"

class SectorNegocio(str, enum.Enum):
    TECNOLOGIA = "TECNOLOGIA"
    COMERCIO = "COMERCIO"
    SERVICIOS = "SERVICIOS"
    INDUSTRIA = "INDUSTRIA"
    AGRICULTURA = "AGRICULTURA"
    CONSTRUCCION = "CONSTRUCCION"
    TRANSPORTE = "TRANSPORTE"
    TURISMO = "TURISMO"
    SALUD = "SALUD"
    EDUCACION = "EDUCACION"
    OTRO = "OTRO"

class NivelEducacion(str, enum.Enum):
    SIN_EDUCACION = "SIN_EDUCACION"
    PRIMARIA = "PRIMARIA"
    SECUNDARIA = "SECUNDARIA"
    TECNICO = "TECNICO"
    UNIVERSITARIO = "UNIVERSITARIO"
    POSTGRADO = "POSTGRADO"

class EstadoEmprendedor(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    PENDIENTE = "PENDIENTE"
    RECHAZADO = "RECHAZADO"

class EstadoNegocio(str, enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    EN_CREACION = "EN_CREACION"
    VERIFICACION_PENDIENTE = "VERIFICACION_PENDIENTE"
    RECHAZADO = "RECHAZADO"

class TipoDocumento(str, enum.Enum):
    RUT = "RUT"
    NIT = "NIT"
    CEDULA = "CEDULA"
    PASAPORTE = "PASAPORTE"
    LICENCIA_COMERCIAL = "LICENCIA_COMERCIAL"
    CAMARA_COMERCIO = "CAMARA_COMERCIO"
    OTRO = "OTRO"

class CategoriaRiesgo(str, enum.Enum):
    MUY_BAJO = "MUY_BAJO"
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"

class TipoModelo(str, enum.Enum):
    ENSEMBLE = "ENSEMBLE"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    LINEAR = "LINEAR"
    VOTING = "VOTING"
    NEURAL_NETWORK = "NEURAL_NETWORK"

class TipoInteraccion(str, enum.Enum):
    CLICK = "CLICK"
    APLICACION = "APLICACION"
    GUARDADO = "GUARDADO"
    VISUALIZACION = "VISUALIZACION"
    COMPARTIDO = "COMPARTIDO"

class EstadoOportunidad(str, enum.Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"
    PAUSADA = "PAUSADA"
    AGOTADA = "AGOTADA"

class TipoOportunidad(str, enum.Enum):
    CREDITO = "CREDITO"
    INVERSION = "INVERSION"
    CAPACITACION = "CAPACITACION"
    NETWORKING = "NETWORKING"
    MENTORIA = "MENTORIA"
    INCUBACION = "INCUBACION"
    CONCURSO = "CONCURSO"
    FONDO_NO_REEMBOLSABLE = "FONDO_NO_REEMBOLSABLE"

class NivelSensibilidad(str, enum.Enum):
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    INSTITUCIONES = "INSTITUCIONES"
    CONSULTORES = "CONSULTORES"
    ANALISTAS = "ANALISTAS"

class CategoriaPrivacidad(str, enum.Enum):
    INFORMACION_PERSONAL = "INFORMACION_PERSONAL"
    FINANCIERA = "FINANCIERA"
    COMERCIAL = "COMERCIAL"
    CONTACTO = "CONTACTO"
    UBICACION = "UBICACION"
    DOCUMENTOS = "DOCUMENTOS"

# ===============================
# Modelos de Usuarios y Roles
# ===============================

class Rol(Base):
    __tablename__ = "roles"  
    rol_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    nivel_permiso = Column(Integer, default=1)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    usuarios = relationship("Usuario", secondary=usuario_rol, back_populates="roles")
    permisos = relationship("Permiso", back_populates="rol")

class Permiso(Base):
    __tablename__ = "permisos"   
    permiso_id = Column(Integer, primary_key=True, index=True)
    rol_id = Column(Integer, ForeignKey("roles.rol_id"))
    modulo = Column(String(100), nullable=False)
    accion = Column(String(100), nullable=False)
    descripcion = Column(Text)
    rol = relationship("Rol", back_populates="permisos")

class Usuario(Base):
    __tablename__ = "usuarios"
    usuario_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    tipo_usuario = Column(SQLEnum(TipoUsuario), nullable=False)
    estado = Column(SQLEnum(EstadoUsuario), default=EstadoUsuario.ACTIVO) 
    nombre_completo = Column(String(255))
    telefono = Column(String(20))
    avatar_url = Column(String(500))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    ultimo_login = Column(DateTime(timezone=True))
    intentos_fallidos = Column(Integer, default=0)
    token_recuperacion = Column(String(255))
    expiracion_token = Column(DateTime(timezone=True))
    roles = relationship("Rol", secondary=usuario_rol, back_populates="usuarios")
    emprendedor = relationship("Emprendedor", back_populates="usuario", uselist=False)
    institucion = relationship("Institucion", back_populates="usuario", uselist=False)
    politicas_aceptadas = relationship("AceptacionPolitica", back_populates="usuario")
    consentimientos = relationship("Consentimiento", back_populates="usuario")
    empleos = relationship("EmpleadoNegocio", back_populates="usuario")

# ===============================
# Modelos de Ubicación Geográfica
# ===============================

class Pais(Base):
    __tablename__ = "paise"   
    pais_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    codigo_iso = Column(String(3))
    emoji = Column(String(10))
    departamentos = relationship("Departamento", back_populates="pais")
    emprendedores = relationship("Emprendedor", back_populates="pais_residencia")
    negocios = relationship("Negocio", back_populates="pais")

class Departamento(Base):
    __tablename__ = "departamento"  
    departamento_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    pais_id = Column(Integer, ForeignKey("paises.pais_id"))
    pais = relationship("Pais", back_populates="departamentos")
    ciudades = relationship("Ciudad", back_populates="departamento")
class Ciudad(Base):
    __tablename__ = "ciudad"
    ciudad_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.departamento_id"))
    latitud = Column(Float)
    longitud = Column(Float)
    departamento = relationship("Departamento", back_populates="ciudades")
    barrios = relationship("Barrio", back_populates="ciudad")
    emprendedores = relationship("Emprendedor", back_populates="ciudad_residencia")
    negocios = relationship("Negocio", back_populates="ciudad")


class Barrio(Base):
    __tablename__ = "barrios"  
    barrio_id = Column(Integer, primary_key=True, index=True)
    ciudad_id = Column(Integer, ForeignKey("ciudades.ciudad_id"))
    nombre = Column(String(100), nullable=False)
    latitud = Column(Float)
    longitud = Column(Float)
    ciudad = relationship("Ciudad", back_populates="barrios")
    emprendedores = relationship("Emprendedor", back_populates="barrio_residencia")
    negocios = relationship("Negocio", back_populates="barrio")

# ===============================
# Modelos de Emprendedores y Negocios
# ===============================

class Emprendedor(Base):
    __tablename__ = "emprendedores"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False, unique=True)
    # Información personal del emprendedor
    biografia = Column(Text)
    experiencia_total = Column(Integer, default=0)
    habilidades = Column(JSON)
    intereses = Column(JSON)
    linkedin_url = Column(String(500))
    sitio_web_personal = Column(String(500))
    # Ubicación personal (diferente a la del negocio)
    pais_residencia_id = Column(Integer, ForeignKey("paises.pais_id"))
    ciudad_residencia_id = Column(Integer, ForeignKey("ciudades.ciudad_id"))
    barrio_residencia_id = Column(Integer, ForeignKey("barrios.barrio_id"))
    direccion_residencia = Column(Text)
    # Preferencias
    preferencia_contacto = Column(String(50), default="EMAIL")
    recibir_notificaciones = Column(Boolean, default=True)
    idiomas = Column(JSON)
    # Estado
    estado = Column(SQLEnum(EstadoEmprendedor), default=EstadoEmprendedor.ACTIVO)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    fecha_verificacion = Column(DateTime(timezone=True))  
    # Relaciones
    usuario = relationship("Usuario", back_populates="emprendedor")
    pais_residencia = relationship("Pais", foreign_keys=[pais_residencia_id])
    ciudad_residencia = relationship("Ciudad", foreign_keys=[ciudad_residencia_id])
    barrio_residencia = relationship("Barrio", foreign_keys=[barrio_residencia_id])
    negocios = relationship("Negocio", back_populates="emprendedor")
    evaluaciones = relationship("EvaluacionRiesgo", back_populates="emprendedor")

class Negocio(Base):
    __tablename__ = "negocios"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedores.id"), nullable=False) 
    # Información básica
    nombre_comercial = Column(String(255), nullable=False)
    razon_social = Column(String(255))
    es_mipyme = Column(Boolean, default=True)
    es_negocio_principal = Column(Boolean, default=False) 
    # Información legal
    tipo_documento = Column(SQLEnum(TipoDocumento))
    numero_documento = Column(String(100))
    fecha_constitucion = Column(DateTime)
    camara_comercio = Column(String(100))    
    # Sector y actividad
    sector_negocio = Column(SQLEnum(SectorNegocio), nullable=False)
    subsector = Column(String(100))
    codigo_ciiu = Column(String(10))
    descripcion_actividad = Column(Text)
    # Información operativa
    experiencia_sector = Column(Integer, default=0)
    meses_operacion = Column(Integer, default=0)
    empleados_directos = Column(Integer, default=0)
    empleados_indirectos = Column(Integer, default=0)
    modelo_negocio = Column(String(255))
    sitio_web = Column(String(500))
    # Información financiera
    ingresos_mensuales_promedio = Column(Float, default=0.0)
    ingresos_anuales = Column(Float, default=0.0)
    capital_trabajo = Column(Float, default=0.0)
    deuda_existente = Column(Float, default=0.0)
    activos_totales = Column(Float, default=0.0)
    pasivos_totales = Column(Float, default=0.0)
    flujo_efectivo_mensual = Column(Float, default=0.0)
    
    # Información de riesgo
    puntaje_credito_negocio = Column(Integer, default=0)
    historial_pagos_negocio = Column(Integer, default=0)
    calificacion_riesgo_negocio = Column(String(50))
    # Ubicación del negocio
    pais_id = Column(Integer, ForeignKey("paises.pais_id"))
    ciudad_id = Column(Integer, ForeignKey("ciudades.ciudad_id"))
    barrio_id = Column(Integer, ForeignKey("barrios.barrio_id"))
    direccion_comercial = Column(Text)
    coordenadas_gps = Column(JSON)
    
    # Contacto comercial
    telefono_comercial = Column(String(20))
    email_comercial = Column(String(255))
    persona_contacto = Column(String(255))
    
    # Estado
    estado = Column(SQLEnum(EstadoNegocio), default=EstadoNegocio.EN_CREACION)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    fecha_verificacion = Column(DateTime(timezone=True))
    usuario_verificacion = Column(Integer, ForeignKey("usuarios.usuario_id"))
    
    # Campos calculados
    edad_negocio = Column(Integer)
    ratio_deuda_ingresos = Column(Float)
    rentabilidad_estimada = Column(Float)
    
    # Relaciones
    emprendedor = relationship("Emprendedor", back_populates="negocios")
    verificador = relationship("Usuario", foreign_keys=[usuario_verificacion])
    pais = relationship("Pais", foreign_keys=[pais_id])
    ciudad = relationship("Ciudad", foreign_keys=[ciudad_id])
    barrio = relationship("Barrio", foreign_keys=[barrio_id])
    
    configuraciones_privacidad = relationship("ConfiguracionPrivacidad", back_populates="negocio")
    documentos = relationship("DocumentoNegocio", back_populates="negocio")
    empleados = relationship("EmpleadoNegocio", back_populates="negocio")
    evaluaciones_riesgo = relationship("EvaluacionRiesgo", back_populates="negocio")
    interacciones = relationship("InteraccionRecomendacion", back_populates="negocio")
    aplicaciones = relationship("AplicacionOportunidad", back_populates="negocio")

# ===============================
# Modelos de IA y Evaluaciones
# ===============================

class ModeloIA(Base):
    __tablename__ = "modelos_ia"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    tipo = Column(SQLEnum(TipoModelo), nullable=False)
    version = Column(String(20), default="1.0")
    accuracy = Column(Float, default=0.0)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    fecha_entrenamiento = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    parametros = Column(JSON)
    ruta_modelo = Column(String(500))
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    es_produccion = Column(Boolean, default=False)

    evaluaciones = relationship("EvaluacionRiesgo", back_populates="modelo")
    historicos = relationship("HistoricoModelo", back_populates="modelo")

class EvaluacionRiesgo(Base):
    __tablename__ = "evaluaciones_riesgo"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedores.id"))
    negocio_id = Column(Integer, ForeignKey("negocios.id"))
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"))
    
    # Probabilidades
    probabilidad_muy_bajo = Column(Float, default=0.0)
    probabilidad_bajo = Column(Float, default=0.0)
    probabilidad_medio = Column(Float, default=0.0)
    probabilidad_alto = Column(Float, default=0.0)
    probabilidad_muy_alto = Column(Float, default=0.0)
    categoria_riesgo = Column(SQLEnum(CategoriaRiesgo), nullable=False)
    puntaje_riesgo = Column(Integer, nullable=False)
    confianza_prediccion = Column(Float)
    
    # Explicaciones
    explicacion_shap = Column(JSON)
    explicacion_lime = Column(JSON)
    explicacion_global = Column(JSON)
    explicacion_final = Column(Text)
    caracteristicas_importantes = Column(JSON)
    
    # Metadata
    fecha_evaluacion = Column(DateTime(timezone=True), server_default=func.now())
    version_modelo = Column(String(20))
    tiempo_procesamiento = Column(Float)
    
    # Relaciones
    emprendedor = relationship("Emprendedor", back_populates="evaluaciones")
    negocio = relationship("Negocio", back_populates="evaluaciones_riesgo")
    modelo = relationship("ModeloIA", back_populates="evaluaciones")

class HistoricoModelo(Base):
    __tablename__ = "historico_modelos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    modelo_ia_id = Column(Integer, ForeignKey("modelos_ia.id"), nullable=False)
    
    # Métricas
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Información del entrenamiento
    fecha_entrenamiento = Column(DateTime(timezone=True), server_default=func.now())
    tamaño_dataset = Column(Integer)
    caracteristicas_utilizadas = Column(JSON)
    tiempo_entrenamiento = Column(Float)
    
    modelo = relationship("ModeloIA", back_populates="historicos")

# ===============================
# Modelos de Oportunidades y Recomendaciones
# ===============================

class Institucion(Base):
    __tablename__ = "instituciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"), unique=True)
    
    nombre = Column(String(255), nullable=False, unique=True)
    tipo = Column(String(100))
    descripcion = Column(Text)
    
    # Información de contacto
    telefono_contacto = Column(String(20))
    email_contacto = Column(String(255))
    persona_contacto = Column(String(255))
    
    # Ubicación
    pais_id = Column(Integer, ForeignKey("paises.pais_id"))
    ciudad_id = Column(Integer, ForeignKey("ciudades.ciudad_id"))
    direccion = Column(Text)
    
    website = Column(String(500))
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="institucion")
    pais = relationship("Pais", foreign_keys=[pais_id])
    ciudad = relationship("Ciudad", foreign_keys=[ciudad_id])
    oportunidades = relationship("Oportunidad", back_populates="institucion")

class Oportunidad(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"))
    
    # Información básica
    nombre = Column(String(255), nullable=False)
    tipo = Column(SQLEnum(TipoOportunidad), nullable=False)
    descripcion = Column(Text)
    beneficios = Column(Text)
    requisitos = Column(Text)
    
    # Criterios de elegibilidad
    sector_compatible = Column(SQLEnum(SectorNegocio))
    riesgo_minimo = Column(SQLEnum(CategoriaRiesgo))
    riesgo_maximo = Column(SQLEnum(CategoriaRiesgo))
    experiencia_minima = Column(Integer, default=0)
    empleados_minimos = Column(Integer, default=0)
    ingresos_minimos = Column(Float, default=0.0)
    capital_minimo = Column(Float, default=0.0)
    nivel_educacion_minimo = Column(SQLEnum(NivelEducacion))
    
    # Información financiera
    monto_minimo = Column(Float, default=0.0)
    monto_maximo = Column(Float, default=0.0)
    tasa_interes = Column(Float)
    plazo_maximo = Column(Integer)
    garantias_requeridas = Column(Text)
    
    # Fechas importantes
    fecha_apertura = Column(DateTime(timezone=True))
    fecha_cierre = Column(DateTime(timezone=True))
    fecha_publicacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Estado
    estado = Column(SQLEnum(EstadoOportunidad), default=EstadoOportunidad.ACTIVA)
    puntaje_similitud_base = Column(Float, default=0.0)
    popularidad = Column(Integer, default=0)
    vistas = Column(Integer, default=0)
    aplicaciones_exitosas = Column(Integer, default=0)
    
    # Información de contacto
    contacto_nombre = Column(String(255))
    contacto_email = Column(String(255))
    contacto_telefono = Column(String(20))
    url_aplicacion = Column(String(500))
    
    # Relaciones
    institucion = relationship("Institucion", back_populates="oportunidades")
    interacciones = relationship("InteraccionRecomendacion", back_populates="oportunidad")
    aplicaciones = relationship("AplicacionOportunidad", back_populates="oportunidad")
    recomendaciones = relationship("Recomendacion", back_populates="oportunidad")

class InteraccionRecomendacion(Base):
    __tablename__ = "interacciones_recomendacion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    oportunidad_id = Column(Integer, ForeignKey("oportunidades.id"), nullable=False)
    
    # Información de la interacción
    tipo_interaccion = Column(SQLEnum(TipoInteraccion), nullable=False)
    rating = Column(Integer)
    tiempo_vista = Column(Integer)
    dispositivo = Column(String(100))
    ubicacion = Column(String(100))
    
    # Información de la recomendación
    algoritmo_recomendacion = Column(String(100))
    puntaje_recomendacion = Column(Float)
    posicion_lista = Column(Integer)
    
    # Metadata
    fecha_interaccion = Column(DateTime(timezone=True), server_default=func.now())
    sesion_id = Column(String(100))
    
    # Relaciones
    negocio = relationship("Negocio", back_populates="interacciones")
    oportunidad = relationship("Oportunidad", back_populates="interacciones")

class AplicacionOportunidad(Base):
    __tablename__ = "aplicaciones_oportunidades"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    oportunidad_id = Column(Integer, ForeignKey("oportunidades.id"), nullable=False)
    
    # Estado de la aplicación
    estado = Column(String(50))
    fecha_aplicacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_decision = Column(DateTime(timezone=True))
    monto_solicitado = Column(Float)
    monto_aprobado = Column(Float)
    
    # Información adicional
    comentarios = Column(Text)
    documentos_adjuntos = Column(JSON)
    puntaje_evaluacion = Column(Float)
    
    # Relaciones
    negocio = relationship("Negocio", back_populates="aplicaciones")
    oportunidad = relationship("Oportunidad", back_populates="aplicaciones")

class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    oportunidad_id = Column(Integer, ForeignKey("oportunidades.id"), nullable=False)
    
    # Puntajes
    puntaje_contenido = Column(Float)
    puntaje_colaborativo = Column(Float)
    puntaje_conocimiento = Column(Float)
    puntaje_final = Column(Float, nullable=False)
    
    # Explicación
    explicacion = Column(Text)
    caracteristicas_compatibles = Column(JSON)
    
    # Metadata
    fecha_recomendacion = Column(DateTime(timezone=True), server_default=func.now())
    algoritmo_utilizado = Column(String(100))
    mostrada = Column(Boolean, default=False)
    clickeada = Column(Boolean, default=False)
    
    # Relaciones
    negocio = relationship("Negocio")
    oportunidad = relationship("Oportunidad", back_populates="recomendaciones")

# ===============================
# Modelos de Privacidad y Documentos
# ===============================

class ConfiguracionPrivacidad(Base):
    __tablename__ = "configuraciones_privacidad"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    
    # Configuración
    categoria = Column(SQLEnum(CategoriaPrivacidad), nullable=False)
    campo = Column(String(100), nullable=False)
    nivel_sensibilidad = Column(SQLEnum(NivelSensibilidad), default=NivelSensibilidad.PRIVADO)
    
    # Autorizaciones
    instituciones_autorizadas = Column(JSON)
    usuarios_autorizados = Column(JSON)
    roles_autorizados = Column(JSON)
    
    # Configuración temporal
    fecha_expiracion = Column(DateTime(timezone=True))
    es_temporal = Column(Boolean, default=False)
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    usuario_configuracion = Column(Integer, ForeignKey("usuarios.usuario_id"))
    
    # Relaciones
    negocio = relationship("Negocio", back_populates="configuraciones_privacidad")
    usuario = relationship("Usuario", foreign_keys=[usuario_configuracion])

class PoliticaPrivacidad(Base):
    __tablename__ = "politicas_privacidad"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    contenido = Column(Text, nullable=False)
    
    # Aplicación
    fecha_implementacion = Column(DateTime(timezone=True), nullable=False)
    fecha_expiracion = Column(DateTime(timezone=True))
    obligatoria = Column(Boolean, default=True)
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    usuario_creacion = Column(Integer, ForeignKey("usuarios.usuario_id"))
    
    # Relaciones
    aceptaciones = relationship("AceptacionPolitica", back_populates="politica")
    usuario = relationship("Usuario", foreign_keys=[usuario_creacion])

class AceptacionPolitica(Base):
    __tablename__ = "aceptaciones_politicas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    politica_id = Column(Integer, ForeignKey("politicas_privacidad.id"), nullable=False)
    
    # Datos de aceptación
    fecha_aceptacion = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    version_aceptada = Column(String(20), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="politicas_aceptadas")
    politica = relationship("PoliticaPrivacidad", back_populates="aceptaciones")

class Consentimiento(Base):
    __tablename__ = "consentimientos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    
    # Tipo de consentimiento
    tipo_consentimiento = Column(String(100), nullable=False)
    proposito = Column(Text, nullable=False)
    instituciones_involucradas = Column(JSON)
    
    # Configuración
    concedido = Column(Boolean, default=False)
    fecha_concesion = Column(DateTime(timezone=True))
    fecha_expiracion = Column(DateTime(timezone=True))
    revocable = Column(Boolean, default=True)
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="consentimientos")
    negocio = relationship("Negocio")

class DocumentoNegocio(Base):
    __tablename__ = "documentos_negocios"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    emprendedor_id = Column(Integer, ForeignKey("emprendedores.id"), nullable=False)
    
    # Información del documento
    tipo_documento = Column(SQLEnum(TipoDocumento), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_almacenamiento = Column(String(500), nullable=False)
    descripcion = Column(Text)
    
    # Metadata
    fecha_documento = Column(DateTime(timezone=True))
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
    tamaño_bytes = Column(Integer)
    mime_type = Column(String(100))
    
    # Privacidad
    nivel_sensibilidad = Column(SQLEnum(NivelSensibilidad), default=NivelSensibilidad.PRIVADO)
    instituciones_autorizadas = Column(JSON)
    
    # Verificación
    verificado = Column(Boolean, default=False)
    fecha_verificacion = Column(DateTime(timezone=True))
    usuario_verificacion = Column(Integer, ForeignKey("usuarios.usuario_id"))
    
    # Relaciones
    negocio = relationship("Negocio", back_populates="documentos")
    emprendedor = relationship("Emprendedor")
    verificador = relationship("Usuario", foreign_keys=[usuario_verificacion])

class EmpleadoNegocio(Base):
    __tablename__ = "empleados_negocios"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    
    # Información del empleado
    cargo = Column(String(100), nullable=False)
    fecha_ingreso = Column(DateTime(timezone=True))
    fecha_retiro = Column(DateTime(timezone=True))
    es_administrador = Column(Boolean, default=False)
    porcentaje_participacion = Column(Float, default=0.0)
    
    # Permisos
    puede_editar = Column(Boolean, default=False)
    puede_ver_finanzas = Column(Boolean, default=False)
    puede_ver_documentos = Column(Boolean, default=False)
    
    # Estado
    estado = Column(String(50), default="ACTIVO")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    negocio = relationship("Negocio", back_populates="empleados")
    usuario = relationship("Usuario", back_populates="empleos")

class HistorialFinanciero(Base):
    __tablename__ = "historial_financiero"

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    
    # Periodo
    año = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    periodo_cerrado = Column(Boolean, default=False)
    
    # Datos financieros
    ingresos = Column(Float, default=0.0)
    gastos = Column(Float, default=0.0)
    utilidad = Column(Float, default=0.0)
    activos = Column(Float, default=0.0)
    pasivos = Column(Float, default=0.0)
    flujo_efectivo = Column(Float, default=0.0)
    
    # Métricas
    margen_utilidad = Column(Float)
    ratio_endeudamiento = Column(Float)
    rotacion_activos = Column(Float)
    
    # Privacidad
    nivel_sensibilidad = Column(SQLEnum(NivelSensibilidad), default=NivelSensibilidad.PRIVADO)
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    negocio = relationship("Negocio")

# ===============================
# Modelos de Auditoría y Configuración
# ===============================

class Auditoria(Base):
    __tablename__ = "auditoria"
    
    auditoria_id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"))
    accion = Column(String(100), nullable=False)
    modulo = Column(String(100), nullable=False)
    descripcion = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    datos_antes = Column(JSON)
    datos_despues = Column(JSON)
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario")

class SesionUsuario(Base):
    __tablename__ = "sesiones_usuarios"
    
    sesion_id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id"))
    token_sesion = Column(String(500), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    dispositivo = Column(String(255))
    activa = Column(Boolean, default=True)
    
    usuario = relationship("Usuario")

class CaracteristicaSistema(Base):
    __tablename__ = "caracteristicas_sistema"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    tipo_dato = Column(String(50))
    importancia_global = Column(Float)
    rango_minimo = Column(Float)
    rango_maximo = Column(Float)
    activa = Column(Boolean, default=True)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())

class ConfiguracionSistema(Base):
    __tablename__ = "configuraciones_sistema"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    clave = Column(String(100), nullable=False, unique=True)
    valor = Column(Text)
    tipo = Column(String(50))
    descripcion = Column(Text)
    categoria = Column(String(100))
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())
    usuario_actualizacion = Column(String(100))

class LogSistema(Base):
    __tablename__ = "logs_sistema"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nivel = Column(String(50))
    modulo = Column(String(100))
    mensaje = Column(Text)
    datos_adicionales = Column(JSON)
    usuario_id = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

# ===============================
# Constraints
# ===============================

__table_args__ = (
    # InteraccionRecomendacion
    CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    CheckConstraint('tiempo_vista >= 0', name='check_tiempo_vista'),
    
    # EvaluacionRiesgo
    CheckConstraint('puntaje_riesgo >= 0 AND puntaje_riesgo <= 100', name='check_puntaje_riesgo_range'),
    CheckConstraint('confianza_prediccion >= 0 AND confianza_prediccion <= 1', name='check_confianza_range'),
    
    # AplicacionOportunidad
    CheckConstraint('monto_solicitado >= 0', name='check_monto_solicitado'),
    CheckConstraint('monto_aprobado >= 0', name='check_monto_aprobado'),
    
    # EmpleadoNegocio
    CheckConstraint('porcentaje_participacion >= 0 AND porcentaje_participacion <= 100', name='check_porcentaje_participacion'),
)



# Conexión a la base de datos PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:12345@localhost:5432/girardot_db"
engine = create_engine(DATABASE_URL)

# Crear tablas
Base.metadata.create_all(engine)

print("✅ Tablas creadas exitosamente en PostgreSQL")






#===============================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Float,Text, JSON,Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Base para los modelos
Base = declarative_base()

# Catálogos
usuario_rol = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuario.usuario_id"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("rol.rol_id"), primary_key=True)
)

# ===============================
# Roles y Usuarios
# ===============================

class Rol(Base):
    __tablename__ = "rol"
    rol_id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)

    usuarios = relationship(
        "Usuario",
        secondary=usuario_rol,
        back_populates="roles"
    )


class Usuario(Base):
    __tablename__ = "usuario"
    usuario_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Guardar hash, no la contraseña
    email = Column(String, unique=True, nullable=False)

    # Relación muchos a muchos
    roles = relationship(
        "Rol",
        secondary=usuario_rol,
        back_populates="usuarios"
    )

class Pais(Base):
    __tablename__ = "pais"
    pais_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    codigo_iso = Column(String(3), nullable=True)
    emoji = Column(String(10), nullable=True)    # emoji de la bandera
    departamentos = relationship("Departamento", back_populates="pais")
    

class Departamento(Base):
    __tablename__ = "departamento"
    departamento_id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    pais_id = Column(Integer, ForeignKey("pais.pais_id"))
    pais = relationship("Pais", back_populates="departamentos")
    ciudades = relationship("Ciudad", back_populates="departamento")
  


class Ciudad(Base):
    __tablename__ = "ciudad"
    ciudad_id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamento.departamento_id"))
    departamento = relationship("Departamento", back_populates="ciudades")
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    barrios = relationship("Barrio", back_populates="ciudad")
  


class Barrio(Base):
    __tablename__ = "barrio"
    barrio_id = Column(Integer, primary_key=True)
    ciudad_id = Column(Integer, ForeignKey("ciudad.ciudad_id"))
    nombre = Column(String, nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    ciudad = relationship("Ciudad", back_populates="barrios")


class Sector(Base):
    __tablename__ = "sector"
    sector_id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)

class Institucion(Base):
    __tablename__ = "institucion"
    institucion_id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String)
    nit = Column(String)

class Emprendedor(Base):
    __tablename__ = "emprendedor"
    emprendedor_id = Column(Integer, primary_key=True)
    nombre = Column(String)
    telefono = Column(String)
    email = Column(String)
    nivel_digital = Column(String)
    fecha_registro = Column(DateTime, server_default=func.now())
    negocios = relationship("Negocio", back_populates="emprendedor")

class Negocio(Base):
    __tablename__ = "negocio"
    negocio_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    sector_id = Column(Integer, ForeignKey("sector.sector_id"))
    formalidad = Column(String)
    ventas_promedio = Column(Numeric)
    antiguedad_meses = Column(Integer)
    barrio_id = Column(Integer, ForeignKey("barrio.barrio_id"))

    emprendedor = relationship("Emprendedor", back_populates="negocios")

class Oportunidad(Base):
    __tablename__ = "oportunidad"
    oportunidad_id = Column(Integer, primary_key=True)
    institucion_id = Column(Integer, ForeignKey("institucion.institucion_id"))
    tipo = Column(String)
    nombre = Column(String, nullable=False)
    requisitos = Column(Text)
    ciudad_destino = Column(String)
    condiciones = Column(JSON)
    elegibilidad = Column(JSON)

class Solicitud(Base):
    __tablename__ = "solicitud"
    solicitud_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    oportunidad_id = Column(Integer, ForeignKey("oportunidad.oportunidad_id"))
    estado = Column(String)
    monto_solicitado = Column(Numeric)
    monto_otorgado = Column(Numeric)
    fecha = Column(DateTime, server_default=func.now())

class EvaluacionRiesgo(Base):
    __tablename__ = "evaluacion_riesgo"
    evaluacion_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    negocio_id = Column(Integer, ForeignKey("negocio.negocio_id"))
    model_version = Column(String)
    score = Column(Numeric)
    label = Column(String)
    shap_top_features = Column(JSON)
    umbral_usado = Column(Numeric)
    fecha = Column(DateTime, server_default=func.now())

class Recomendacion(Base):
    __tablename__ = "recomendacion"
    recomendacion_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    oportunidad_id = Column(Integer, ForeignKey("oportunidad.oportunidad_id"))
    algoritmo = Column(String)
    score = Column(Numeric)
    rank = Column(Integer)
    fue_aceptada = Column(Boolean)
    fecha = Column(DateTime, server_default=func.now())

class InteraccionAsistente(Base):
    __tablename__ = "interaccion_asistente"
    interaccion_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    canal = Column(String)
    intencion = Column(String)
    payload = Column(JSON)
    fecha = Column(DateTime, server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    oportunidad_id = Column(Integer, ForeignKey("oportunidad.oportunidad_id"))
    rating = Column(Integer)
    comentario = Column(Text)
    fecha = Column(DateTime, server_default=func.now())

class Consentimiento(Base):
    __tablename__ = "consentimiento"
    consentimiento_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    alcance = Column(String)
    firmado_en = Column(DateTime, server_default=func.now())
    vence_en = Column(DateTime)
    vigente = Column(Boolean, default=True)

class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshot"
    snapshot_id = Column(Integer, primary_key=True)
    emprendedor_id = Column(Integer, ForeignKey("emprendedor.emprendedor_id"))
    version_pipeline = Column(String)
    features = Column(JSON)
    fecha_snapshot = Column(DateTime, server_default=func.now())



# Conexión a la base de datos PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:12345@localhost:5432/girardot_db"
engine = create_engine(DATABASE_URL)

# Crear tablas
Base.metadata.create_all(engine)

print("✅ Tablas creadas exitosamente en PostgreSQL")
'''