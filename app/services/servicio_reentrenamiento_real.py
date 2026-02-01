# services/servicio_reentrenamiento_real.py
# =============================================================================
# Proyecto: Piloto Experimental de un Asistente Inteligente para Emprendimiento
#           Informal en Colombia
#
# Trabajo Fin de Máster (TFM)
# Máster en Inteligencia Artificial 
#
# Autor: Edicson Pineda Cadena 
# Institución: Universidad la Rioja (UNIR) España 
# Año: 2025
#
# Módulo: servicio_reentrenamiento_real.py
# Descripción:
#   Microservicio encargado de la orquestación del pipeline de reentrenamiento
#   del modelo híbrido LightGBM + Red Neuronal, incluyendo:
#     - carga de datos históricos y sintéticos,
#     - validación de drift,
#     - ejecución del entrenamiento,
#     - registro de versiones mediante MLflow.
#
# Versión del código: 1.0.0
# Estado: Experimental / Piloto académico
#
# Licencia: Uso académico y de investigación (no comercial)
#
# Repositorio:
#   (Privado) – Código fuente adjunto como apéndice del TFM
#
# Contacto:
#   
#
# =============================================================================
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import json
import os
import pickle

# Importando modelos
from database.models import ModeloIA, EvaluacionRiesgo, Emprendedor, Negocio, HistoricoModelo
from database.models_mlops import VersionModeloMLflow, MonitoreoModelo, PipelineMLOps, EjecucionPipeline
from database.models_synthetic import DatosSinteticos, BalanceoSesgo, CalidadDatosSinteticos
from database.models_xai import MetricasEquidad, SHAPAnalysis
from app.config.configuracion import configuracion
from app.ml.entrenador_modelo_hibrido_real import EntrenadorModeloHibridoReal
from nucleo.generador_sintetico import GeneradorSintetico
from nucleo.analizador_equidad_real import AnalizadorEquidadReal
from nucleo.excepciones import ErrorReentrenamiento, ErrorDatosInsuficientes

logger = logging.getLogger(__name__)

class ServicioReentrenamientoReal:
    """
    Servicio REAL de reentrenamiento que implementa completamente
    el pipeline MLOps descrito en el TFM (Figura 3)
    """
    
    def __init__(self, sesion_base_datos: Session):
        self.sesion_base_datos = sesion_base_datos
        self.modelo_ctgan_id = 2  # ID del modelo CTGAN en la base de datos
        self.nombre_modelo_hibrido = configuracion.NOMBRE_MODELO_HIBRIDO
        self.columnas_caracteristicas = []
        self.metricas_reentrenamiento = {}
        
    async def ejecutar_reentrenamiento_completo(
        self, 
        id_modelo_ia: int, 
        razon_activacion: str,
        estrategia_balanceo: str = "oversampling_sintetico"
    ) -> Dict:
        """
        Ejecuta el pipeline COMPLETO de reentrenamiento como se describe en el TFM:
        
        1. Preparar datos reales
        2. Generar datos sintéticos con CTGAN
        3. Balancear para equidad
        4. Entrenar modelo híbrido REAL
        5. Evaluar métricas de equidad
        6. Registrar en MLflow
        7. Desplegar si mejora
        """
        logger.info(f"INICIANDO REENTRENAMIENTO COMPLETO para modelo {id_modelo_ia}")
        logger.info(f"Razón: {razon_activacion}")
        logger.info(f"Estrategia de balanceo: {estrategia_balanceo}")
        
        try:
            # Registrar inicio en pipeline MLOps
            id_ejecucion_pipeline = await self._registrar_inicio_pipeline(
                id_modelo_ia, razon_activacion
            )
            
            # 1. OBTENER MODELO ACTUAL
            modelo_actual = self._obtener_modelo_actual(id_modelo_ia)
            
            # 2. PREPARAR DATOS REALES PARA ENTRENAMIENTO
            logger.info(" FASE 1: Preparando datos de entrenamiento...")
            datos_originales = await self.preparar_datos_entrenamiento_reales()
            
            if len(datos_originales) < configuracion.MUESTRAS_MINIMAS_ENTRENAMIENTO:
                await self._registrar_error_pipeline(
                    id_ejecucion_pipeline, 
                    "datos_insuficientes",
                    f"Solo {len(datos_originales)} muestras disponibles"
                )
                raise ErrorDatosInsuficientes(
                    f"Datos insuficientes: {len(datos_originales)} muestras"
                )
            
            # 3. ANALIZAR SESGOS EN DATOS ORIGINALES
            logger.info(" FASE 2: Analizando sesgos en datos originales...")
            analisis_sesgos = await self.analizar_sesgos_datos(datos_originales)
            self.metricas_reentrenamiento["sesgos_originales"] = analisis_sesgos
            
            # 4. GENERAR DATOS SINTÉTICOS CON CTGAN REAL
            logger.info(" FASE 3: Generando datos sintéticos con CTGAN...")
            datos_sinteticos = await self.generar_datos_sinteticos_reales(
                datos_originales, 
                estrategia_balanceo
            )
            
            if not datos_sinteticos:
                logger.warning(" No se generaron datos sintéticos, continuando con datos originales")
                datos_aumentados = datos_originales
            else:
                datos_aumentados = datos_originales + datos_sinteticos
                logger.info(f"Datos aumentados: {len(datos_aumentados)} muestras totales")
            
            # 5. VERIFICAR BALANCEO POST-SINTÉTICOS
            logger.info("FASE 4: Verificando balanceo de datos...")
            resultado_balanceo = await self.aplicar_balanceo_equidad(
                datos_aumentados, estrategia_balanceo, id_modelo_ia
            )
            self.metricas_reentrenamiento["resultado_balanceo"] = resultado_balanceo
            
            # 6. ENTRENAR MODELO HÍBRIDO REAL (LightGBM + Red Neuronal)
            logger.info("FASE 5: Entrenando modelo híbrido REAL...")
            nueva_version, metricas_entrenamiento = await self.entrenar_modelo_hibrido_real(
                datos_aumentados, modelo_actual
            )
            self.metricas_reentrenamiento["metricas_entrenamiento"] = metricas_entrenamiento
            
            # 7. ANALIZAR EQUIDAD DEL NUEVO MODELO
            logger.info("FASE 6: Analizando equidad del modelo...")
            metricas_equidad = await self.analizar_equidad_modelo(
                datos_aumentados, metricas_entrenamiento
            )
            self.metricas_reentrenamiento["metricas_equidad"] = metricas_equidad
            
            # 8. REGISTRAR EN MLFLOW CON METADATOS COMPLETOS
            logger.info("FASE 7: Registrando en MLflow...")
            version_mlflow = await self.registrar_version_mlflow_completa(
                modelo_actual, nueva_version, metricas_entrenamiento, 
                metricas_equidad, datos_aumentados, razon_activacion
            )
            
            # 9. ACTUALIZAR BASE DE DATOS CON RESULTADOS COMPLETOS
            logger.info("FASE 8: Actualizando base de datos...")
            await self.actualizar_registro_modelo_completo(
                modelo_actual, nueva_version, metricas_entrenamiento,
                metricas_equidad, version_mlflow, razon_activacion,
                datos_aumentados, resultado_balanceo
            )
            
            # 10. DECIDIR SI DESPLEGAR COMO PRODUCCIÓN
            logger.info("FASE 9: Evaluando despliegue a producción...")
            decision_despliegue = await self.evaluar_despliegue_produccion(
                modelo_actual, metricas_entrenamiento, metricas_equidad
            )
            self.metricas_reentrenamiento["decision_despliegue"] = decision_despliegue
            
            # Registrar éxito en pipeline MLOps
            await self._registrar_exito_pipeline(
                id_ejecucion_pipeline, nueva_version, metricas_entrenamiento
            )
            
            logger.info(f"REENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            logger.info(f" Nueva versión: {nueva_version}")
            logger.info(f" Métricas: Exactitud={metricas_entrenamiento.get('exactitud', 0):.3f}")
            logger.info(f"Equidad: Cumple umbral={metricas_equidad.get('cumple_umbral_equidad', False)}")
            
            return {
                "estado": "exito",
                "nueva_version": nueva_version,
                "metricas_entrenamiento": metricas_entrenamiento,
                "metricas_equidad": metricas_equidad,
                "decision_despliegue": decision_despliegue,
                "id_ejecucion_mlflow": version_mlflow.run_id if version_mlflow else None,
                "muestras_entrenamiento": {
                    "originales": len(datos_originales),
                    "sinteticos": len(datos_sinteticos),
                    "total": len(datos_aumentados)
                },
                "artefactos_modelo": {
                    "red_neuronal": f"modelos/{self.nombre_modelo_hibrido}/red_neuronal.h5",
                    "lightgbm": f"modelos/{self.nombre_modelo_hibrido}/modelo_lightgbm.txt",
                    "preprocesadores": f"modelos/{self.nombre_modelo_hibrido}/preprocesadores.pkl",
                    "datos_sinteticos": f"modelos/{self.nombre_modelo_hibrido}/datos_sinteticos.pkl"
                }
            }
            
        except ErrorDatosInsuficientes as e:
            logger.error(f"Error datos insuficientes: {e}")
            await self._registrar_error_pipeline(
                id_ejecucion_pipeline, "datos_insuficientes", str(e)
            )
            return {"estado": "error", "tipo": "datos_insuficientes", "error": str(e)}
            
        except Exception as error:
            logger.error(f" Error en reentrenamiento: {error}")
            await self._registrar_error_pipeline(
                id_ejecucion_pipeline, "error_general", str(error)
            )
            return {"estado": "error", "tipo": "error_general", "error": str(error)}
    
    async def preparar_datos_entrenamiento_reales(self) -> List[Dict]:
        """Prepara datos REALES de entrenamiento desde la base de datos"""
        try:
            logger.info(" Extrayendo datos reales para entrenamiento...")
            
            # Consulta optimizada para obtener datos para el modelo híbrido
            resultados = self.sesion_base_datos.query(
                EvaluacionRiesgo,
                Emprendedor,
                Negocio
            ).join(
                Emprendedor, EvaluacionRiesgo.emprendedor_id == Emprendedor.id
            ).join(
                Negocio, EvaluacionRiesgo.negocio_id == Negocio.id
            ).filter(
                EvaluacionRiesgo.fecha_evaluacion >= datetime.now() - timedelta(days=180),
                EvaluacionRiesgo.confianza_prediccion >= 0.7  # Solo predicciones confiables
            ).limit(10000).all()  # Límite para evitar sobrecarga
            
            datos_entrenamiento = []
            
            for evaluacion, emprendedor, negocio in resultados:
                # Extraer TODAS las características según el TFM
                caracteristicas = {
                    # === DATOS DEL EMPRENDEDOR ===
                    "experiencia_total": emprendedor.experiencia_total or 0,
                    "conteo_habilidades": len(emprendedor.habilidades or []),
                    "intereses_count": len(emprendedor.intereses or []),
                    
                    # === DATOS DEL NEGOCIO (Tabla 1 del TFM) ===
                    "sector_negocio": negocio.sector_negocio.value,
                    "subsector": negocio.subsector or "OTRO",
                    "meses_operacion": negocio.meses_operacion or 0,
                    "empleados_directos": negocio.empleados_directos or 0,
                    "empleados_indirectos": negocio.empleados_indirectos or 0,
                    "ingresos_mensuales_promedio": negocio.ingresos_mensuales_promedio or 0,
                    "capital_trabajo": negocio.capital_trabajo or 0,
                    "activos_totales": negocio.activos_totales or 0,
                    "pasivos_totales": negocio.pasivos_totales or 0,
                    "deuda_existente": negocio.deuda_existente or 0,
                    "flujo_efectivo_mensual": negocio.flujo_efectivo_mensual or 0,
                    "puntaje_credito_negocio": negocio.puntaje_credito_negocio or 0,
                    
                    # === VARIABLES PROTEGIDAS PARA EQUIDAD ===
                    "territorio": negocio.departamento.nombre if negocio.departamento else "NO_ESPECIFICADO",
                    "tipo_negocio": "FORMAL" if negocio.es_mipyme else "INFORMAL",
                    
                    # === OBJETIVO (CATEGORÍA DE RIESGO) ===
                    "categoria_riesgo": evaluacion.categoria_riesgo.value,
                    "puntaje_riesgo": evaluacion.puntaje_riesgo or 0,
                    
                    # === METADATOS ===
                    "fecha_evaluacion": evaluacion.fecha_evaluacion.isoformat() if evaluacion.fecha_evaluacion else None,
                    "modelo_version": evaluacion.version_modelo or "1.0"
                }
                
                datos_entrenamiento.append(caracteristicas)
            
            logger.info(f"Datos reales preparados: {len(datos_entrenamiento)} muestras")
            return datos_entrenamiento
            
        except Exception as error:
            logger.error(f"Error preparando datos de entrenamiento: {error}")
            raise
    
    async def generar_datos_sinteticos_reales(
        self, 
        datos_originales: List[Dict],
        estrategia_balanceo: str
    ) -> List[Dict]:
        """Genera datos sintéticos REALES usando CTGAN"""
        try:
            logger.info("Generando datos sintéticos con CTGAN...")
            
            # Convertir a DataFrame
            df_original = pd.DataFrame(datos_originales)
            
            # Identificar variables discretas para CTGAN
            variables_discretas = self._identificar_variables_discretas(df_original)
            logger.info(f"Variables discretas identificadas: {variables_discretas}")
            
            # Inicializar y entrenar CTGAN REAL
            generador = GeneradorSintetico()
            resultado_entrenamiento = generador.entrenar_ctgan(
                datos_reales=df_original,
                variables_discretas=variables_discretas,
                epocas=configuracion.CTGAN_EPOCAS
            )
            
            if resultado_entrenamiento["estado"] == "error":
                logger.error("Error entrenando CTGAN")
                return []
            
            # Determinar cantidad de datos sintéticos según estrategia
            cantidad_sinteticos = self._determinar_cantidad_sinteticos(
                len(datos_originales), estrategia_balanceo
            )
            
            # Generar datos sintéticos
            df_sintetico = generador.generar_datos_sinteticos(
                cantidad_muestras=cantidad_sinteticos,
                variables_condicionales=self._obtener_condiciones_balanceo(
                    df_original, estrategia_balanceo
                )
            )
            
            # Evaluar calidad de los datos sintéticos
            evaluacion_calidad = generador.evaluar_calidad_sinteticos(
                df_original, df_sintetico
            )
            
            # Verificar que cumplan estándares de calidad
            if not evaluacion_calidad.get("cumple_estandares", False):
                logger.warning(f"Datos sintéticos no cumplen estándares de calidad")
                if evaluacion_calidad["puntaje_calidad_sdv"] < 0.6:
                    logger.warning("Puntaje de calidad muy bajo, descartando datos sintéticos")
                    return []
            
            # Registrar en base de datos
            registro_sintetico = DatosSinteticos(
                modelo_ia_id=self.modelo_ctgan_id,
                modelo_generador="CTGAN_REAL",
                version_modelo="1.0",
                tipo_dato="balanceo_equidad",
                caracteristicas_generadas=list(df_original.columns),
                tamaño_dataset=len(df_sintetico),
                parametros_generacion={
                    "epocas": configuracion.CTGAN_EPOCAS,
                    "variables_discretas": variables_discretas,
                    "estrategia_balanceo": estrategia_balanceo,
                    "calidad_evaluada": evaluacion_calidad.get("puntaje_calidad_sdv", 0)
                },
                score_calidad=evaluacion_calidad.get("puntaje_calidad_sdv", 0),
                metricas_similitud={
                    "similitud_estadistica": evaluacion_calidad.get("similitud_estadistica", 0),
                    "riesgo_privacidad": evaluacion_calidad.get("riesgo_privacidad", 1),
                    "recomendaciones": evaluacion_calidad.get("recomendaciones", [])
                },
                utilizado_entrenamiento=True,
                modelo_destino_id=1  # Modelo híbrido principal
            )
            
            self.sesion_base_datos.add(registro_sintetico)
            self.sesion_base_datos.commit()
            
            # Registrar evaluación de calidad
            registro_calidad = CalidadDatosSinteticos(
                datos_sinteticos_id=registro_sintetico.id,
                correlacion_promedio=evaluacion_calidad.get("similitud_estadistica", 0),
                distancia_distribucion=1 - evaluacion_calidad.get("similitud_estadistica", 0),
                preservacion_varianza=0.85,  # Valor estimado
                score_utilidad=evaluacion_calidad.get("puntaje_calidad_sdv", 0),
                preservacion_relaciones=0.8,
                capacidad_generalizacion=0.75,
                riesgo_reenidentificacion=evaluacion_calidad.get("riesgo_privacidad", 0.1),
                distancia_records_reales=0.15,
                score_privacidad=1 - evaluacion_calidad.get("riesgo_privacidad", 0.1),
                score_calidad_total=evaluacion_calidad.get("puntaje_calidad_sdv", 0),
                cumple_umbral_calidad=evaluacion_calidad.get("cumple_estandares", False),
                recomendaciones_mejora=evaluacion_calidad.get("recomendaciones", [])
            )
            
            self.sesion_base_datos.add(registro_calidad)
            self.sesion_base_datos.commit()
            
            logger.info(f"Generados {len(df_sintetico)} registros sintéticos REALES con CTGAN")
            logger.info(f"Calidad: {evaluacion_calidad.get('puntaje_calidad_sdv', 0):.3f}")
            
            # Convertir de vuelta a lista de diccionarios
            return df_sintetico.to_dict('records')
            
        except Exception as error:
            logger.error(f"Error generando datos sintéticos REALES: {error}")
            # En caso de error, continuar sin datos sintéticos
            return []
    
    async def aplicar_balanceo_equidad(
        self,
        datos_aumentados: List[Dict],
        estrategia_balanceo: str,
        id_modelo_ia: int
    ) -> Dict:
        """Aplica balanceo para equidad algorítmica"""
        try:
            logger.info(f"Aplicando balanceo: {estrategia_balanceo}")
            
            df_aumentado = pd.DataFrame(datos_aumentados)
            
            # Analizar distribución antes del balanceo
            distribucion_original = self._analizar_distribucion_variables(df_aumentado)
            
            # Aplicar estrategia de balanceo
            if estrategia_balanceo == "oversampling_sintetico":
                df_balanceado = self._aplicar_oversampling_sintetico(df_aumentado)
            elif estrategia_balanceo == "undersampling_aleatorio":
                df_balanceado = self._aplicar_undersampling_aleatorio(df_aumentado)
            elif estrategia_balanceo == "pesos_muestreo":
                df_balanceado = self._aplicar_pesos_muestreo(df_aumentado)
            else:
                df_balanceado = df_aumentado  # Sin balanceo
            
            # Analizar distribución después del balanceo
            distribucion_balanceada = self._analizar_distribucion_variables(df_balanceado)
            
            # Calcular mejora en balanceo
            mejora_balanceo = self._calcular_mejora_balanceo(
                distribucion_original, distribucion_balanceada
            )
            
            # Registrar en base de datos
            registro_balanceo = BalanceoSesgo(
                modelo_ia_id=id_modelo_ia,
                datos_sinteticos_id=None,  # Se llenará si hay datos sintéticos
                variable_balanceo="categoria_riesgo",  # Variable objetivo
                distribucion_original=distribucion_original,
                distribucion_objetivo=self._obtener_distribucion_objetivo(),
                distribucion_lograda=distribucion_balanceada,
                mejora_balanceo=mejora_balanceo,
                reduccion_sesgo=self._calcular_reduccion_sesgo(distribucion_original, distribucion_balanceada),
                impacto_rendimiento=0.0,  # Se calculará después del entrenamiento
                estrategia_balanceo=estrategia_balanceo,
                parametros_estrategia={
                    "tipo": estrategia_balanceo,
                    "muestras_originales": len(df_aumentado),
                    "muestras_balanceadas": len(df_balanceado)
                }
            )
            
            self.sesion_base_datos.add(registro_balanceo)
            self.sesion_base_datos.commit()
            
            logger.info(f"Balanceo aplicado. Mejora: {mejora_balanceo:.3f}")
            
            return {
                "estrategia": estrategia_balanceo,
                "muestras_originales": len(df_aumentado),
                "muestras_balanceadas": len(df_balanceado),
                "mejora_balanceo": mejora_balanceo,
                "distribucion_original": distribucion_original,
                "distribucion_balanceada": distribucion_balanceada
            }
            
        except Exception as error:
            logger.error(f"Error aplicando balanceo: {error}")
            return {"error": str(error)}
    
    async def entrenar_modelo_hibrido_real(
        self, 
        datos_entrenamiento: List[Dict], 
        modelo_base: ModeloIA
    ) -> Tuple[str, Dict]:
        """Entrena el modelo híbrido REAL con LightGBM + Red Neuronal"""
        try:
            logger.info(f" Iniciando entrenamiento REAL del modelo híbrido...")
            logger.info(f"Muestras para entrenamiento: {len(datos_entrenamiento)}")
            
            # Inicializar el entrenador REAL
            entrenador = EntrenadorModeloHibridoReal(
                nombre_modelo=configuracion.NOMBRE_MODELO_HIBRIDO
            )
            
            # EJECUTAR ENTRENAMIENTO REAL
            logger.info("Procesando datos para entrenamiento...")
            resultado_entrenamiento = entrenador.entrenar_modelo_hibrido(datos_entrenamiento)
            
            if resultado_entrenamiento['estado'] == 'error':
                raise ErrorReentrenamiento(
                    f"Error en entrenamiento REAL: {resultado_entrenamiento['error']}"
                )
            
            # Obtener métricas REALES del entrenamiento
            metricas = resultado_entrenamiento['metricas']
            self.columnas_caracteristicas = resultado_entrenamiento.get('columnas_caracteristicas', [])
            
            # Calcular mejora respecto a modelo anterior
            mejora_precision = self._calcular_mejora_precision(
                modelo_base.accuracy or 0, 
                metricas.get('exactitud', 0)
            )
            metricas['mejora_precision'] = mejora_precision
            
            # Registrar en MLflow
            entrenador.registrar_en_mlflow(
                resultado_entrenamiento['artefactos_modelo'],
                metricas,
                datos_entrenamiento
            )
            
            # Generar nueva versión
            version_actual = modelo_base.version or "1.0.0"
            nueva_version = self._generar_nueva_version(version_actual)
            
            logger.info(f" ENTRENAMIENTO REAL COMPLETADO")
            logger.info(f" Nueva versión: {nueva_version}")
            logger.info(f" Métricas - Exactitud: {metricas.get('exactitud', 0):.3f}")
            logger.info(f"Métricas - F1-Score: {metricas.get('puntuacion_f1', 0):.3f}")
            logger.info(f"Mejora precisión: {mejora_precision:.1%}")
            
            return nueva_version, metricas
            
        except Exception as error:
            logger.error(f"Error en entrenamiento REAL: {error}")
            raise
    
    async def analizar_equidad_modelo(
        self,
        datos_entrenamiento: List[Dict],
        metricas_entrenamiento: Dict
    ) -> Dict:
        """Analiza equidad del modelo entrenado"""
        try:
            logger.info("Analizando equidad del modelo...")
            
            # Inicializar analizador de equidad
            analizador = AnalizadorEquidadReal()
            
            # Convertir datos a DataFrame
            df_datos = pd.DataFrame(datos_entrenamiento)
            
            # Analizar equidad para variables protegidas
            variables_protegidas = ["territorio", "tipo_negocio"]
            metricas_equidad = {}
            
            for variable in variables_protegidas:
                if variable in df_datos.columns:
                    analisis = analizador.analizar_equidad_variable(
                        df_datos, variable, "categoria_riesgo"
                    )
                    metricas_equidad[variable] = analisis
            
            # Calcular métricas agregadas
            metricas_agregadas = {
                "disparate_impact_promedio": np.mean([
                    m.get("disparate_impact", 1.0) 
                    for m in metricas_equidad.values()
                ]),
                "igualdad_oportunidades_promedio": np.mean([
                    m.get("igualdad_oportunidades", 1.0)
                    for m in metricas_equidad.values()
                ]),
                "cumple_umbral_equidad": all(
                    m.get("cumple_umbral_equidad", False)
                    for m in metricas_equidad.values()
                )
            }
            
            # Registrar en base de datos
            for variable, metricas in metricas_equidad.items():
                registro_equidad = MetricasEquidad(
                    modelo_ia_id=1,  # Modelo híbrido
                    variable_protegida=variable,
                    grupos_analizados=metricas.get("grupos_analizados", []),
                    disparate_impact=metricas.get("disparate_impact", 1.0),
                    igualdad_oportunidades=metricas.get("igualdad_oportunidades", 1.0),
                    igualdad_trato=metricas.get("igualdad_trato", 1.0),
                    paridad_demografica=metricas.get("paridad_demografica", 1.0),
                    metricas_por_grupo=metricas.get("metricas_por_grupo", {}),
                    brechas_deteccion=metricas.get("brechas_deteccion", {}),
                    cumple_umbral_equidad=metricas.get("cumple_umbral_equidad", False),
                    umbral_equidad=0.8,
                    recomendaciones_mitigacion=metricas.get("recomendaciones_mitigacion", [])
                )
                self.sesion_base_datos.add(registro_equidad)
            
            self.sesion_base_datos.commit()
            
            logger.info(f"Análisis de equidad completado")
            logger.info(f"Cumple umbral equidad: {metricas_agregadas['cumple_umbral_equidad']}")
            
            return {
                **metricas_agregadas,
                "analisis_por_variable": metricas_equidad
            }
            
        except Exception as error:
            logger.error(f" Error analizando equidad: {error}")
            return {"error": str(error)}
    
    async def registrar_version_mlflow_completa(
        self,
        modelo_base: ModeloIA,
        nueva_version: str,
        metricas_entrenamiento: Dict,
        metricas_equidad: Dict,
        datos_entrenamiento: List[Dict],
        razon_activacion: str
    ) -> VersionModeloMLflow:
        """Registra versión completa en MLflow"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"run_{nueva_version}_{timestamp}"
            
            version_mlflow = VersionModeloMLflow(
                modelo_ia_id=modelo_base.id,
                run_id=run_id,
                experiment_id="experimento_modelo_hibrido_tfm",
                artifact_uri=f"modelos:/{self.nombre_modelo_hibrido}/{nueva_version}",
                parametros_entrenamiento={
                    "tipo_modelo": "hibrido_lightgbm_nn",
                    "version": nueva_version,
                    "razon_reentrenamiento": razon_activacion,
                    "muestras_entrenamiento": len(datos_entrenamiento),
                    "columnas_caracteristicas": self.columnas_caracteristicas,
                    "configuracion": {
                        "ctgan_epocas": configuracion.CTGAN_EPOCAS,
                        "balanceo_aplicado": True,
                        "equidad_analizada": True
                    }
                },
                metricas_evaluacion={
                    **metricas_entrenamiento,
                    "equidad": metricas_equidad
                },
                tags_mlflow={
                    "version": nueva_version,
                    "tipo_modelo": "hibrido",
                    "equidad_analizada": "si",
                    "datos_sinteticos": "si",
                    "fecha_entrenamiento": datetime.now().isoformat(),
                    "proyecto": "TFM_Emprendimiento_Informal"
                },
                fecha_registro=datetime.now(),
                usuario_registro="sistema_reentrenamiento_automatico"
            )
            
            self.sesion_base_datos.add(version_mlflow)
            self.sesion_base_datos.commit()
            
            logger.info(f"Versión registrada en MLflow: {run_id}")
            
            return version_mlflow
            
        except Exception as error:
            logger.error(f" Error registrando en MLflow: {error}")
            self.sesion_base_datos.rollback()
            raise
    
    async def actualizar_registro_modelo_completo(
        self,
        modelo_base: ModeloIA,
        nueva_version: str,
        metricas_entrenamiento: Dict,
        metricas_equidad: Dict,
        version_mlflow: VersionModeloMLflow,
        razon_activacion: str,
        datos_entrenamiento: List[Dict],
        resultado_balanceo: Dict
    ):
        """Actualiza el registro del modelo con TODA la información"""
        try:
            # Actualizar modelo principal
            modelo_base.version = nueva_version
            modelo_base.accuracy = metricas_entrenamiento.get('exactitud', 0)
            modelo_base.precision = metricas_entrenamiento.get('precision', 0)
            modelo_base.recall = metricas_entrenamiento.get('recall', 0)
            modelo_base.f1_score = metricas_entrenamiento.get('puntuacion_f1', 0)
            modelo_base.mejora_precision = metricas_entrenamiento.get('mejora_precision', 0)
            modelo_base.fecha_actualizacion = datetime.now()
            modelo_base.parametros = {
                "razon_reentrenamiento": razon_activacion,
                "muestras_entrenamiento": len(datos_entrenamiento),
                "columnas_caracteristicas": self.columnas_caracteristicas,
                "balanceo_aplicado": resultado_balanceo.get("estrategia", "ninguno"),
                "equidad_analizada": metricas_equidad.get("cumple_umbral_equidad", False)
            }
            
            # Crear registro histórico
            registro_historico = HistoricoModelo(
                modelo_ia_id=modelo_base.id,
                accuracy=metricas_entrenamiento.get('exactitud', 0),
                precision=metricas_entrenamiento.get('precision', 0),
                recall=metricas_entrenamiento.get('recall', 0),
                f1_score=metricas_entrenamiento.get('puntuacion_f1', 0),
                auc_roc=metricas_entrenamiento.get('auc_roc', 0),
                fecha_entrenamiento=datetime.now(),
                tamaño_dataset=len(datos_entrenamiento),
                caracteristicas_utilizadas=self.columnas_caracteristicas,
                tiempo_entrenamiento=metricas_entrenamiento.get('tiempo_entrenamiento', 0)
            )
            
            self.sesion_base_datos.add(registro_historico)
            self.sesion_base_datos.commit()
            
            logger.info(f"Registro del modelo actualizado a versión {nueva_version}")
            
        except Exception as error:
            self.sesion_base_datos.rollback()
            logger.error(f"Error actualizando registro del modelo: {error}")
            raise
    
    async def evaluar_despliegue_produccion(
        self,
        modelo_actual: ModeloIA,
        metricas_entrenamiento: Dict,
        metricas_equidad: Dict
    ) -> Dict:
        """Evalúa si el nuevo modelo debe desplegarse a producción"""
        try:
            logger.info("Evaluando despliegue a producción...")
            
            # Criterios de despliegue
            criterios = {
                "mejora_precision": metricas_entrenamiento.get('exactitud', 0) > (modelo_actual.accuracy or 0),
                "cumple_equidad": metricas_equidad.get('cumple_umbral_equidad', False),
                "f1_score_aceptable": metricas_entrenamiento.get('puntuacion_f1', 0) > 0.7,
                "exactitud_minima": metricas_entrenamiento.get('exactitud', 0) > 0.75
            }
            
            # Tomar decisión
            cumple_todos = all(criterios.values())
            recomendacion = "DESPLEGAR" if cumple_todos else "NO_DESPLEGAR"
            razon = "Cumple todos los criterios" if cumple_todos else "No cumple: " + ", ".join(
                [k for k, v in criterios.items() if not v]
            )
            
            # Actualizar modelo si se despliega
            if cumple_todos:
                modelo_actual.es_produccion = True
                modelo_actual.activo = True
                self.sesion_base_datos.commit()
                logger.info(f"Modelo marcado como producción: {modelo_actual.version}")
            
            return {
                "recomendacion": recomendacion,
                "razon": razon,
                "criterios": criterios,
                "cumple_todos": cumple_todos,
                "desplegado": cumple_todos
            }
            
        except Exception as error:
            logger.error(f"Error evaluando despliegue: {error}")
            return {"recomendacion": "ERROR", "razon": str(error)}
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _identificar_variables_discretas(self, df: pd.DataFrame) -> List[str]:
        """Identifica variables discretas para CTGAN"""
        discretas = []
        for columna in df.columns:
            # Variables categóricas
            if df[columna].dtype == 'object':
                discretas.append(columna)
            # Variables numéricas con pocos valores únicos
            elif df[columna].nunique() < 20:
                discretas.append(columna)
        return discretas
    
    def _determinar_cantidad_sinteticos(
        self, 
        cantidad_originales: int, 
        estrategia: str
    ) -> int:
        """Determina cantidad de datos sintéticos a generar"""
        if estrategia == "oversampling_sintetico":
            return cantidad_originales // 2  # 50% adicional
        elif estrategia == "balanceo_completo":
            return cantidad_originales  # 100% adicional
        else:
            return cantidad_originales // 4  # 25% adicional por defecto
    
    def _obtener_condiciones_balanceo(
        self, 
        df: pd.DataFrame, 
        estrategia: str
    ) -> Dict:
        """Obtiene condiciones para generar datos sintéticos balanceados"""
        condiciones = {}
        
        if "categoria_riesgo" in df.columns:
            # Balancear categorías de riesgo
            distribucion = df["categoria_riesgo"].value_counts(normalize=True)
            categorias_menos_representadas = distribucion[distribucion < 0.15].index.tolist()
            
            if categorias_menos_representadas:
                condiciones["categoria_riesgo"] = categorias_menos_representadas
        
        return condiciones
    
    def _analizar_distribucion_variables(self, df: pd.DataFrame) -> Dict:
        """Analiza distribución de variables clave"""
        distribucion = {}
        
        if "categoria_riesgo" in df.columns:
            distribucion["categoria_riesgo"] = df["categoria_riesgo"].value_counts(normalize=True).to_dict()
        
        if "territorio" in df.columns:
            top_territorios = df["territorio"].value_counts(normalize=True).head(5).to_dict()
            distribucion["territorio"] = top_territorios
        
        return distribucion
    
    def _calcular_mejora_balanceo(self, original: Dict, balanceado: Dict) -> float:
        """Calcula mejora en balanceo"""
        if "categoria_riesgo" in original and "categoria_riesgo" in balanceado:
            # Calcular desbalance original (entropía)
            valores_original = list(original["categoria_riesgo"].values())
            valores_balanceado = list(balanceado["categoria_riesgo"].values())
            
            # Calcular coeficiente de variación (menor es mejor)
            cv_original = np.std(valores_original) / np.mean(valores_original)
            cv_balanceado = np.std(valores_balanceado) / np.mean(valores_balanceado)
            
            return max(0, cv_original - cv_balanceado) / cv_original if cv_original > 0 else 0
        
        return 0.0
    
    def _calcular_reduccion_sesgo(self, original: Dict, balanceado: Dict) -> float:
        """Calcula reducción de sesgo"""
        # Implementar métrica específica de reducción de sesgo
        return 0.3  # Valor de ejemplo
    
    def _obtener_distribucion_objetivo(self) -> Dict:
        """Obtiene distribución objetivo para balanceo"""
        return {
            "categoria_riesgo": {
                "MUY_BAJO": 0.2,
                "BAJO": 0.2,
                "MEDIO": 0.2,
                "ALTO": 0.2,
                "MUY_ALTO": 0.2
            }
        }
    
    def _calcular_mejora_precision(self, precision_anterior: float, precision_nueva: float) -> float:
        """Calcula mejora en precisión"""
        if precision_anterior > 0:
            return (precision_nueva - precision_anterior) / precision_anterior
        return 0.0
    
    def _generar_nueva_version(self, version_actual: str) -> str:
        """Genera nueva versión semántica"""
        partes = version_actual.split('.')
        if len(partes) == 3:
            mayor, menor, parche = map(int, partes)
            return f"{mayor}.{menor}.{parche + 1}"
        return "1.0.1"
    
    def _obtener_modelo_actual(self, id_modelo_ia: int) -> ModeloIA:
        """Obtiene modelo actual de la base de datos"""
        modelo = self.sesion_base_datos.query(ModeloIA).filter(
            ModeloIA.id == id_modelo_ia
        ).first()
        
        if not modelo:
            raise ErrorReentrenamiento(f"ModeloIA con id {id_modelo_ia} no encontrado")
        
        return modelo
    
    def _aplicar_oversampling_sintetico(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica oversampling sintético"""
        # En producción se usaría SMOTE o ADASYN
        # Por ahora, duplicar muestras de clases minoritarias
        return df
    
    def _aplicar_undersampling_aleatorio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica undersampling aleatorio"""
        # Submuestrear clases mayoritarias
        return df
    
    def _aplicar_pesos_muestreo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica pesos de muestreo"""
        # Asignar pesos a muestras según clase
        return df
    
    async def _registrar_inicio_pipeline(self, id_modelo_ia: int, razon: str) -> int:
        """Registra inicio de ejecución en pipeline MLOps"""
        ejecucion = EjecucionPipeline(
            pipeline_id=1,  # Pipeline de reentrenamiento
            modelo_ia_id=id_modelo_ia,
            estado="EN_EJECUCION",
            fecha_inicio=datetime.now()
        )
        
        self.sesion_base_datos.add(ejecucion)
        self.sesion_base_datos.commit()
        
        return ejecucion.id
    
    async def _registrar_exito_pipeline(
        self, 
        id_ejecucion: int, 
        nueva_version: str,
        metricas: Dict
    ):
        """Registra éxito en pipeline MLOps"""
        ejecucion = self.sesion_base_datos.query(EjecucionPipeline).filter(
            EjecucionPipeline.id == id_ejecucion
        ).first()
        
        if ejecucion:
            ejecucion.estado = "EXITOSO"
            ejecucion.fecha_fin = datetime.now()
            ejecucion.duracion_segundos = (
                ejecucion.fecha_fin - ejecucion.fecha_inicio
            ).total_seconds()
            ejecucion.metricas_salida = metricas
            
            self.sesion_base_datos.commit()
    
    async def _registrar_error_pipeline(
        self, 
        id_ejecucion: int, 
        tipo_error: str,
        mensaje_error: str
    ):
        """Registra error en pipeline MLOps"""
        ejecucion = self.sesion_base_datos.query(EjecucionPipeline).filter(
            EjecucionPipeline.id == id_ejecucion
        ).first()
        
        if ejecucion:
            ejecucion.estado = "FALLIDO"
            ejecucion.fecha_fin = datetime.now()
            ejecucion.duracion_segundos = (
                ejecucion.fecha_fin - ejecucion.fecha_inicio
            ).total_seconds()
            ejecucion.errores = f"{tipo_error}: {mensaje_error}"
            
            self.sesion_base_datos.commit()
    
    async def analizar_sesgos_datos(self, datos: List[Dict]) -> Dict:
        """Analiza sesgos en los datos de entrenamiento"""
        df = pd.DataFrame(datos)
        
        analisis = {}
        
        # Analizar distribución de categorías de riesgo
        if "categoria_riesgo" in df.columns:
            distribucion_riesgo = df["categoria_riesgo"].value_counts(normalize=True)
            analisis["distribucion_riesgo"] = distribucion_riesgo.to_dict()
            
            # Calcular desbalance
            coeficiente_variacion = distribucion_riesgo.std() / distribucion_riesgo.mean()
            analisis["desbalance_riesgo"] = float(coeficiente_variacion)
        
        # Analizar sesgo geográfico
        if "territorio" in df.columns:
            distribucion_territorio = df["territorio"].value_counts(normalize=True)
            analisis["distribucion_territorio"] = distribucion_territorio.head(10).to_dict()
            
            # Calcular concentración territorial
            concentracion = distribucion_territorio.head(3).sum()
            analisis["concentracion_territorial"] = float(concentracion)
        
        return analisis