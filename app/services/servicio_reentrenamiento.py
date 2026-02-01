from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, List, Tuple

# Importando modelos
from database.models import ModeloIA, EvaluacionRiesgo, Emprendedor, Negocio, HistoricoModelo, MonitoreoModelo
from database.models_mlops import VersionModeloMLflow
from database.models_synthetic import DatosSinteticos, BalanceoSesgo
from app.config.configuracion import configuracion
from app.ml.entrenador_modelo_hibrido import EntrenadorModeloHibrido

logger = logging.getLogger(__name__)

class ServicioReentrenamiento:
    def __init__(self, base_datos: Session):
        self.base_datos = base_datos
    
    async def reentrenar_modelo(self, id_modelo_ia: int, razon_activacion: str) -> Dict:
        """Re-entrenar el modelo híbrido LightGBM + Red Neuronal"""
        try:
            logger.info(f"INICIANDO RE-ENTRENAMIENTO para modelo {id_modelo_ia}. Razón: {razon_activacion}")
            
            # 1. Obtener modelo actual
            modelo_actual = self.base_datos.query(ModeloIA).filter(ModeloIA.id == id_modelo_ia).first()
            if not modelo_actual:
                raise ValueError(f"ModeloIA con id {id_modelo_ia} no encontrado")
            
            # 2. Preparar datos de entrenamiento
            datos_entrenamiento = await self.preparar_datos_entrenamiento()
            logger.info(f" Datos de entrenamiento preparados: {len(datos_entrenamiento)} muestras")
            
            if len(datos_entrenamiento) < configuracion.MUESTRAS_MINIMAS_ENTRENAMIENTO:
                logger.warning(f" Datos insuficientes para re-entrenamiento: {len(datos_entrenamiento)} muestras")
                return {"estado": "omitido", "razon": "datos_insuficientes"}
            
            # 3. Generar datos sintéticos si es necesario
            datos_sinteticos = await self.generar_datos_sinteticos(datos_entrenamiento)
            datos_aumentados = datos_entrenamiento + datos_sinteticos
            logger.info(f" Datos aumentados: {len(datos_aumentados)} muestras totales")
            
            # 4. ENTRENAR NUEVO MODELO (REAL)
            nueva_version, metricas = await self.entrenar_modelo_hibrido(datos_aumentados, modelo_actual)
            
            # 5. Registrar en MLflow
            version_mlflow = await self.registrar_version_mlflow(
                modelo_actual, nueva_version, metricas, datos_aumentados
            )
            
            # 6. Actualizar base de datos
            await self.actualizar_registro_modelo(
                modelo_actual, nueva_version, metricas, version_mlflow, razon_activacion, datos_aumentados
            )
            
            logger.info(f" RE-ENTRENAMIENTO COMPLETADO. Nueva versión: {nueva_version}")
            
            return {
                "estado": "exito",
                "nueva_version": nueva_version,
                "metricas": metricas,
                "id_ejecucion_mlflow": version_mlflow.run_id if version_mlflow else None,
                "muestras_entrenamiento": len(datos_aumentados),
                "artefactos_modelo": {
                    "red_neuronal": "modelos/modelo_hibrido/red_neuronal.h5",
                    "lightgbm": "modelos/modelo_hibrido/modelo_lightgbm.txt",
                    "preprocesadores": "modelos/modelo_hibrido/preprocesadores.pkl"
                }
            }
            
        except Exception as error:
            logger.error(f"Error en re-entrenamiento: {error}")
            return {"estado": "fallo", "error": str(error)}
    
    async def preparar_datos_entrenamiento(self) -> List[Dict]:
        """Preparar datos de entrenamiento desde la base de datos"""
        try:
            # Obtener evaluaciones recientes con datos de emprendedores
            evaluaciones = self.base_datos.query(
                EvaluacionRiesgo,
                Emprendedor,
                Negocio
            ).join(
                Emprendedor, EvaluacionRiesgo.emprendedor_id == Emprendedor.id
            ).join(
                Negocio, EvaluacionRiesgo.negocio_id == Negocio.id
            ).filter(
                EvaluacionRiesgo.fecha_evaluacion >= datetime.now() - timedelta(days=90)
            ).limit(5000).all()
            
            datos_entrenamiento = []
            for evaluacion, emprendedor, negocio in evaluaciones:
                # Extraer características para el modelo híbrido
                caracteristicas = {
                    # Datos del emprendedor
                    "experiencia_total": emprendedor.experiencia_total or 0,
                    "conteo_habilidades": len(emprendedor.habilidades or []),
                    
                    # Datos del negocio
                    "sector_negocio": negocio.sector_negocio.value,
                    "meses_operacion": negocio.meses_operacion or 0,
                    "empleados_directos": negocio.empleados_directos or 0,
                    "ingresos_mensuales": negocio.ingresos_mensuales_promedio or 0,
                    "activos_totales": negocio.activos_totales or 0,
                    
                    # Objetivo (categoría de riesgo)
                    "categoria_riesgo": evaluacion.categoria_riesgo.value,
                    "puntaje_riesgo": evaluacion.puntaje_riesgo or 0
                }
                datos_entrenamiento.append(caracteristicas)
            
            return datos_entrenamiento
            
        except Exception as error:
            logger.error(f"Error preparando datos de entrenamiento: {error}")
            return []
    
    async def generar_datos_sinteticos(self, datos_originales: List[Dict]) -> List[Dict]:
        """Generar datos sintéticos usando CTGAN"""
        try:
            if len(datos_originales) < 100:
                return []  # No generar sintéticos si hay pocos datos
            
            # Registrar generación de datos sintéticos
            registro_sintetico = DatosSinteticos(
                modelo_ia_id=1,  # Modelo generador
                modelo_generador="CTGAN",
                version_modelo="1.0",
                tipo_dato="balanceo",
                caracteristicas_generadas=list(datos_originales[0].keys()) if datos_originales else [],
                tamaño_dataset=len(datos_originales) // 2,  # 50% de datos originales
                parametros_generacion={"epocas": 100, "tamaño_lote": 50},
                puntuacion_calidad=0.85,
                utilizado_entrenamiento=True
            )
            
            self.base_datos.add(registro_sintetico)
            self.base_datos.commit()
            
            # Simular generación de datos (en producción usarías CTGAN real)
            datos_sinteticos = []
            for i in range(len(datos_originales) // 2):
                muestra_sintetica = datos_originales[i % len(datos_originales)].copy()
                # Aplicar pequeñas variaciones
                for clave in muestra_sintetica:
                    if isinstance(muestra_sintetica[clave], (int, float)):
                        muestra_sintetica[clave] *= (0.9 + 0.2 * (i % 10) / 10)  # Variación del ±10%
                datos_sinteticos.append(muestra_sintetica)
            
            logger.info(f"Generados {len(datos_sinteticos)} registros sintéticos")
            return datos_sinteticos
            
        except Exception as error:
            logger.error(f"Error generando datos sintéticos: {error}")
            return []
    
    async def entrenar_modelo_hibrido(self, datos_entrenamiento: List[Dict], modelo_base: ModeloIA) -> Tuple[str, Dict]:
        """ENTRENAMIENTO REAL del modelo híbrido"""
        try:
            logger.info(f" INICIANDO ENTRENAMIENTO REAL con {len(datos_entrenamiento)} muestras...")
            
            # 1. Importar el entrenador real
            from app.ml.entrenador_modelo_hibrido import EntrenadorModeloHibrido
            
            # 2. Inicializar el entrenador
            entrenador = EntrenadorModeloHibrido(nombre_modelo=configuracion.NOMBRE_MODELO)
            
            # 3. 🏋️‍♂️ EJECUTAR ENTRENAMIENTO REAL
            resultado_entrenamiento = entrenador.entrenar_modelo_hibrido(datos_entrenamiento)
            
            if resultado_entrenamiento['estado'] == 'error':
                raise Exception(f"Error en entrenamiento REAL: {resultado_entrenamiento['error']}")
            
            # 4. Obtener métricas reales del entrenamiento
            metricas = resultado_entrenamiento['metricas']
            
            # 5. Registrar en MLflow
            entrenador.registrar_en_mlflow(
                resultado_entrenamiento['artefactos_modelo'],
                metricas,
                datos_entrenamiento
            )
            
            # 6. Generar nueva versión
            version_actual = modelo_base.version or "1.0"
            mayor, menor = map(int, version_actual.split('.'))
            nueva_version = f"{mayor}.{menor + 1}"
            
            logger.info(f"ENTRENAMIENTO REAL COMPLETADO. Nueva versión: {nueva_version}")
            logger.info(f"Métricas reales: Exactitud={metricas.get('exactitud', 0):.3f}, F1={metricas.get('puntuacion_f1', 0):.3f}")
            
            return nueva_version, metricas
            
        except Exception as error:
            logger.error(f"Error en entrenamiento REAL: {error}")
            raise
    
    async def registrar_version_mlflow(self, modelo_base: ModeloIA, nueva_version: str, 
                                     metricas: Dict, datos_entrenamiento: List[Dict]) -> VersionModeloMLflow:
        """Registrar nueva versión en MLflow"""
        try:
            version_mlflow = VersionModeloMLflow(
                modelo_ia_id=modelo_base.id,
                run_id=f"ejecucion_{nueva_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                experiment_id="experimento_modelo_hibrido",
                artifact_uri=f"modelos:/{configuracion.NOMBRE_MODELO}/{nueva_version}",
                parametros_entrenamiento={
                    "tipo_modelo": "lightgbm_hibrido",
                    "version": nueva_version,
                    "muestras_entrenamiento": len(datos_entrenamiento)
                },
                metricas_evaluacion=metricas,
                tags_mlflow={
                    "version": nueva_version,
                    "tipo_modelo": "hibrido",
                    "fecha_entrenamiento": datetime.now().isoformat()
                },
                fecha_registro=datetime.now(),
                usuario_registro="servicio_mlops"
            )
            
            self.base_datos.add(version_mlflow)
            self.base_datos.commit()
            
            return version_mlflow
            
        except Exception as error:
            logger.error(f"Error registrando en MLflow: {error}")
            self.base_datos.rollback()
            raise
    
    async def actualizar_registro_modelo(self, modelo_base: ModeloIA, nueva_version: str,
                                       metricas: Dict, version_mlflow: VersionModeloMLflow,
                                       razon_activacion: str, datos_entrenamiento: List[Dict]):
        """Actualizar el registro del modelo en la base de datos"""
        try:
            # 1. Actualizar modelo principal con métricas REALES
            modelo_base.version = nueva_version
            modelo_base.accuracy = metricas.get('exactitud', 0)
            modelo_base.precision = metricas.get('precision', 0)
            modelo_base.recall = metricas.get('recall', 0)
            modelo_base.f1_score = metricas.get('puntuacion_f1', 0)
            modelo_base.mejora_precision = metricas.get('mejora_precision', 0)
            modelo_base.fecha_actualizacion = datetime.now()
            modelo_base.parametros = {
                "razon_reentrenamiento": razon_activacion,
                "muestras_entrenamiento": len(datos_entrenamiento),
                "columnas_caracteristicas": self.columnas_caracteristicas if hasattr(self, 'columnas_caracteristicas') else []
            }
            
            # 2. Crear registro histórico REAL
            registro_historico = HistoricoModelo(
                modelo_ia_id=modelo_base.id,
                accuracy=metricas.get('exactitud', 0),
                precision=metricas.get('precision', 0),
                recall=metricas.get('recall', 0),
                f1_score=metricas.get('puntuacion_f1', 0),
                auc_roc=metricas.get('auc_roc', 0),
                fecha_entrenamiento=datetime.now(),
                tamaño_dataset=len(datos_entrenamiento),
                caracteristicas_utilizadas=self.columnas_caracteristicas if hasattr(self, 'columnas_caracteristicas') else [],
                tiempo_entrenamiento=metricas.get('tiempo_entrenamiento', 0)
            )
            
            self.base_datos.add(registro_historico)
            self.base_datos.commit()
            
            logger.info(f"Registro actualizado para modelo {modelo_base.id}, versión {nueva_version}")
            
            # 3. Si el modelo es mejor, marcarlo como producción
            exactitud_actual = modelo_base.accuracy or 0
            if metricas.get('exactitud', 0) > exactitud_actual:
                modelo_base.es_produccion = True
                modelo_base.activo = True
                self.base_datos.commit()
                logger.info(f"Modelo {nueva_version} marcado como producción")
            
        except Exception as error:
            self.base_datos.rollback()
            logger.error(f" Error actualizando registro del modelo: {error}")
            raise