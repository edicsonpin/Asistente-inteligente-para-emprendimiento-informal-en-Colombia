# nucleo/generador_sintetico.py -


import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from scipy import stats

# ✅ CORRECCIÓN 1: Import unificado usando SDV (más completo)
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.evaluation.single_table import evaluate_quality, run_diagnostic
from sdv.metrics.tabular import KSComplement, CSTest, LogisticDetection, CorrelationSimilarity

logger = logging.getLogger(__name__)

class GeneradorSintetico:
    """Generador REAL de datos sintéticos usando CTGAN como en el TFM"""
    
    def __init__(self):
        self.modelo_ctgan = None
        self.entrenado = False
        self.metadata = None
        self.scaler = StandardScaler()  # ✅ Para normalización en cálculo de privacidad
        self.datos_entrenamiento_escalados = None  # ✅ Para riesgo de privacidad
    
    def entrenar_ctgan(
        self,
        datos_reales: pd.DataFrame,
        variables_discretas: List[str] = None,
        epocas: int = 300
    ) -> Dict:
        """
        Entrena CTGAN REAL con datos reales
        
        ✅ CORRECCIÓN: Usa SDV correctamente con metadata
        """
        try:
            logger.info(f"🤖 Entrenando CTGAN con {len(datos_reales)} muestras...")
            
            # ✅ CORRECCIÓN 1: Crear metadata para SDV
            self.metadata = SingleTableMetadata()
            self.metadata.detect_from_dataframe(datos_reales)
            
            # ✅ Especificar variables discretas si se proporcionan
            if variables_discretas:
                for var in variables_discretas:
                    if var in datos_reales.columns:
                        self.metadata.update_column(
                            column_name=var,
                            sdtype='categorical'
                        )
                        logger.debug(f"   Variable categórica: {var}")
            
            # ✅ Inicializar CTGAN con configuración del TFM
            self.modelo_ctgan = CTGANSynthesizer(
                metadata=self.metadata,
                epochs=epocas,
                verbose=True,
                enforce_min_max_values=True,  # Respetar rangos
                enforce_rounding=True,  # Redondear valores discretos
                # Hiperparámetros óptimos según literatura
                generator_dim=(256, 256),
                discriminator_dim=(256, 256),
                batch_size=500,
                discriminator_steps=1,
                log_frequency=True
            )
            
            # ✅ Preparar datos para cálculo de privacidad posterior
            datos_numericos = datos_reales.select_dtypes(include=[np.number])
            if len(datos_numericos.columns) > 0:
                self.datos_entrenamiento_escalados = self.scaler.fit_transform(datos_numericos)
            
            # ✅ Entrenar modelo
            logger.info("📚 Iniciando entrenamiento de CTGAN...")
            self.modelo_ctgan.fit(datos_reales)
            
            self.entrenado = True
            
            logger.info("✅ CTGAN entrenado exitosamente")
            
            return {
                "estado": "exito",
                "muestras_entrenamiento": len(datos_reales),
                "epocas": epocas,
                "dimension_sintetica": datos_reales.shape[1],
                "variables_categoricas": len(variables_discretas) if variables_discretas else 0,
                "metadata": self.metadata.to_dict()
            }
            
        except Exception as error:
            logger.error(f"❌ Error entrenando CTGAN: {error}")
            return {"estado": "error", "error": str(error)}
    
    def generar_datos_sinteticos(
        self,
        cantidad_muestras: int,
        variables_condicionales: Dict = None
    ) -> pd.DataFrame:
        """
        Genera datos sintéticos REALES usando CTGAN entrenado
        
        ✅ Validación robusta antes de generar
        """
        if not self.entrenado or self.modelo_ctgan is None:
            raise ValueError("CTGAN no está entrenado. Llame a entrenar_ctgan primero.")
        
        if cantidad_muestras <= 0:
            raise ValueError(f"cantidad_muestras debe ser positiva: {cantidad_muestras}")
        
        try:
            logger.info(f"🎲 Generando {cantidad_muestras} muestras sintéticas...")
            
            # ✅ Generar muestras sintéticas
            muestras_sinteticas = self.modelo_ctgan.sample(
                num_rows=cantidad_muestras,
                output_file_path=None  # No guardar en disco
            )
            
            # ✅ Aplicar condiciones si se especifican
            if variables_condicionales:
                muestras_sinteticas = self._aplicar_condiciones(
                    muestras_sinteticas, variables_condicionales
                )
            
            logger.info(f"✅ Generadas {len(muestras_sinteticas)} muestras sintéticas")
            
            return muestras_sinteticas
            
        except Exception as error:
            logger.error(f"❌ Error generando datos sintéticos: {error}")
            raise
    
    def _aplicar_condiciones(
        self,
        datos: pd.DataFrame,
        condiciones: Dict
    ) -> pd.DataFrame:
        """
        Aplica condiciones a los datos sintéticos
        
        ✅ Mejorado: Validación de columnas existentes
        """
        datos_filtrados = datos.copy()
        
        for variable, valor in condiciones.items():
            if variable not in datos.columns:
                logger.warning(f"⚠️ Variable '{variable}' no existe en datos sintéticos")
                continue
            
            # Filtrar o ajustar según la condición
            if isinstance(valor, (list, tuple)):
                # Mantener solo valores que estén en la lista
                datos_filtrados = datos_filtrados[datos_filtrados[variable].isin(valor)]
            else:
                # Asignar valor fijo
                datos_filtrados[variable] = valor
        
        if len(datos_filtrados) == 0:
            logger.warning("⚠️ Condiciones muy restrictivas, no quedan datos")
            return datos
        
        return datos_filtrados
    
    def evaluar_calidad_sinteticos(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> Dict:
        """
        ✅ CORRECCIÓN 2: Evalúa la calidad usando SDV correctamente
        """
        try:
            logger.info("📊 Evaluando calidad de datos sintéticos...")
            
            # ✅ CORRECCIÓN: Usar evaluate_quality correctamente
            quality_report = evaluate_quality(
                real_data=datos_reales,
                synthetic_data=datos_sinteticos,
                metadata=self.metadata
            )
            
            # Obtener puntaje global
            puntaje_calidad_sdv = quality_report.get_score()
            
            logger.info(f"   Puntaje SDV: {puntaje_calidad_sdv:.3f}")
            
            # ✅ Calcular métricas adicionales detalladas
            metricas_detalladas = self._calcular_metricas_detalladas(
                datos_reales, datos_sinteticos
            )
            
            # ✅ CORRECCIÓN 3: Calcular riesgo de privacidad REAL
            riesgo_privacidad = self._calcular_riesgo_privacidad_real(
                datos_reales, datos_sinteticos
            )
            
            logger.info(f"   Riesgo de privacidad: {riesgo_privacidad:.3f}")
            
            # Combinar resultados
            cumple_estandares = (
                puntaje_calidad_sdv > 0.7 and 
                riesgo_privacidad < 0.1 and
                metricas_detalladas["similitud_estadistica"] > 0.7
            )
            
            resultado = {
                "puntaje_calidad_sdv": float(puntaje_calidad_sdv),
                "similitud_estadistica": metricas_detalladas["similitud_estadistica"],
                "similitud_correlaciones": metricas_detalladas["similitud_correlaciones"],
                "deteccion_sinteticos": metricas_detalladas["deteccion_sinteticos"],
                "riesgo_privacidad": riesgo_privacidad,
                "cumple_estandares": cumple_estandares,
                "recomendaciones": self._generar_recomendaciones_calidad(
                    puntaje_calidad_sdv, riesgo_privacidad, metricas_detalladas
                ),
                "detalles_metricas": metricas_detalladas["detalles"]
            }
            
            logger.info(
                f"{'✅' if cumple_estandares else '⚠️'} Cumple estándares: {cumple_estandares}"
            )
            
            return resultado
            
        except Exception as error:
            logger.error(f"❌ Error evaluando calidad sintética: {error}")
            return {
                "puntaje_calidad_sdv": 0,
                "similitud_estadistica": 0,
                "riesgo_privacidad": 1,
                "cumple_estandares": False,
                "error": str(error)
            }
    
    def _calcular_metricas_detalladas(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> Dict:
        """
        ✅ CORRECCIÓN 4: Métricas de similitud estadística completas
        """
        metricas = []
        detalles = {}
        
        # 1. KS Complement para variables numéricas
        columnas_numericas = datos_reales.select_dtypes(include=[np.number]).columns
        ks_scores = []
        
        for columna in columnas_numericas:
            try:
                ks_score = KSComplement.compute(
                    real_data=datos_reales[[columna]],
                    synthetic_data=datos_sinteticos[[columna]],
                    metadata=self.metadata
                )
                ks_scores.append(ks_score)
                detalles[f"ks_{columna}"] = float(ks_score)
            except Exception as e:
                logger.warning(f"Error calculando KS para {columna}: {e}")
        
        # 2. Chi-Cuadrado para variables categóricas
        columnas_categoricas = datos_reales.select_dtypes(
            include=['object', 'category']
        ).columns
        cs_scores = []
        
        for columna in columnas_categoricas:
            try:
                cs_score = CSTest.compute(
                    real_data=datos_reales[[columna]],
                    synthetic_data=datos_sinteticos[[columna]],
                    metadata=self.metadata
                )
                cs_scores.append(cs_score)
                detalles[f"cs_{columna}"] = float(cs_score)
            except Exception as e:
                logger.warning(f"Error calculando CS para {columna}: {e}")
        
        # 3. Similitud de correlaciones
        try:
            corr_similarity = CorrelationSimilarity.compute(
                real_data=datos_reales,
                synthetic_data=datos_sinteticos,
                metadata=self.metadata
            )
            metricas.append(corr_similarity)
            detalles["similitud_correlaciones"] = float(corr_similarity)
        except Exception as e:
            logger.warning(f"Error calculando similitud de correlaciones: {e}")
            corr_similarity = 0.0
        
        # 4. Detección de sintéticos (cuán distinguibles son)
        try:
            detection_score = LogisticDetection.compute(
                real_data=datos_reales,
                synthetic_data=datos_sinteticos,
                metadata=self.metadata
            )
            # Invertir: queremos que sean difíciles de distinguir
            deteccion_normalizada = 1 - detection_score
            detalles["deteccion_sinteticos"] = float(detection_score)
        except Exception as e:
            logger.warning(f"Error calculando detección: {e}")
            deteccion_normalizada = 0.5
        
        # Combinar todas las métricas
        todas_metricas = ks_scores + cs_scores + [corr_similarity, deteccion_normalizada]
        similitud_promedio = np.mean(todas_metricas) if todas_metricas else 0.0
        
        return {
            "similitud_estadistica": float(similitud_promedio),
            "similitud_correlaciones": float(corr_similarity),
            "deteccion_sinteticos": float(deteccion_normalizada),
            "ks_promedio": float(np.mean(ks_scores)) if ks_scores else 0.0,
            "cs_promedio": float(np.mean(cs_scores)) if cs_scores else 0.0,
            "detalles": detalles
        }
    
    def _calcular_riesgo_privacidad_real(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> float:
        """
        ✅ CORRECCIÓN 3: Calcula riesgo de re-identificación REAL
        
        Basado en:
        1. Distancia mínima a registros reales (k-anonimato)
        2. Proximidad de atributos sensibles
        3. Riesgo de linkage attack
        """
        try:
            # Obtener solo columnas numéricas comunes
            columnas_numericas = list(
                set(datos_reales.select_dtypes(include=[np.number]).columns) &
                set(datos_sinteticos.select_dtypes(include=[np.number]).columns)
            )
            
            if not columnas_numericas:
                logger.warning("⚠️ No hay columnas numéricas para calcular riesgo de privacidad")
                return 0.5
            
            # Normalizar datos
            real_scaled = self.scaler.transform(datos_reales[columnas_numericas])
            sint_scaled = self.scaler.transform(datos_sinteticos[columnas_numericas])
            
            # 1. Calcular distancia mínima de cada registro sintético a datos reales
            nbrs = NearestNeighbors(n_neighbors=1, algorithm='ball_tree', metric='euclidean')
            nbrs.fit(real_scaled)
            
            distancias, indices = nbrs.kneighbors(sint_scaled)
            distancia_minima = distancias.flatten()
            
            # 2. Métricas de privacidad
            distancia_promedio = float(np.mean(distancia_minima))
            distancia_mediana = float(np.median(distancia_minima))
            percentil_5 = float(np.percentile(distancia_minima, 5))
            
            logger.debug(f"   Distancia promedio: {distancia_promedio:.4f}")
            logger.debug(f"   Distancia mediana: {distancia_mediana:.4f}")
            logger.debug(f"   Percentil 5%: {percentil_5:.4f}")
            
            # 3. Calcular riesgo
            # Umbral: si distancia < 0.1, alto riesgo de re-identificación
            UMBRAL_RIESGO_ALTO = 0.1
            UMBRAL_RIESGO_MEDIO = 0.3
            
            # Contar registros sintéticos muy cercanos a reales
            registros_riesgo_alto = np.sum(distancia_minima < UMBRAL_RIESGO_ALTO)
            registros_riesgo_medio = np.sum(
                (distancia_minima >= UMBRAL_RIESGO_ALTO) & 
                (distancia_minima < UMBRAL_RIESGO_MEDIO)
            )
            
            proporcion_riesgo_alto = registros_riesgo_alto / len(distancia_minima)
            proporcion_riesgo_medio = registros_riesgo_medio / len(distancia_minima)
            
            # 4. Calcular riesgo final (0-1)
            # Mayor peso a registros de alto riesgo
            riesgo_final = (
                proporcion_riesgo_alto * 0.8 +
                proporcion_riesgo_medio * 0.4 +
                max(0, 1 - (distancia_promedio / 0.5)) * 0.2
            )
            
            # Normalizar a [0, 1]
            riesgo_final = float(np.clip(riesgo_final, 0, 1))
            
            logger.debug(f"   Registros alto riesgo: {registros_riesgo_alto}/{len(distancia_minima)}")
            logger.debug(f"   Riesgo final: {riesgo_final:.4f}")
            
            return riesgo_final
            
        except Exception as error:
            logger.error(f"❌ Error calculando riesgo de privacidad: {error}")
            return 0.5  # Riesgo medio por defecto
    
    def _generar_recomendaciones_calidad(
        self,
        puntaje_calidad: float,
        riesgo_privacidad: float,
        metricas_detalladas: Dict
    ) -> List[str]:
        """
        ✅ CORRECCIÓN 5: Recomendaciones basadas en múltiples métricas
        """
        recomendaciones = []
        
        # Calidad general baja
        if puntaje_calidad < 0.6:
            recomendaciones.append(
                "🔄 Aumentar épocas de entrenamiento del CTGAN (actual < 300)"
            )
            recomendaciones.append(
                "📊 Aumentar tamaño del batch_size si hay suficientes datos"
            )
        
        if puntaje_calidad < 0.7:
            recomendaciones.append(
                "🎯 Especificar correctamente variables discretas en el entrenamiento"
            )
            recomendaciones.append(
                "⚖️ Verificar balance de clases en datos de entrenamiento"
            )
        
        # Similitud estadística baja
        if metricas_detalladas.get("similitud_estadistica", 0) < 0.7:
            recomendaciones.append(
                "📈 Similitud estadística baja: Aumentar generator_dim a (512, 512)"
            )
            recomendaciones.append(
                "🔍 Revisar preprocesamiento de datos (outliers, valores faltantes)"
            )
        
        # Correlaciones no preservadas
        if metricas_detalladas.get("similitud_correlaciones", 0) < 0.75:
            recomendaciones.append(
                "🔗 Correlaciones no preservadas: Considerar aumentar discriminator_dim"
            )
        
        # Riesgo de privacidad alto
        if riesgo_privacidad > 0.15:
            recomendaciones.append(
                "🔒 Riesgo de privacidad elevado: Aplicar differential privacy"
            )
            recomendaciones.append(
                "📉 Reducir cantidad de muestras sintéticas generadas"
            )
        
        if riesgo_privacidad > 0.1:
            recomendaciones.append(
                "🛡️ Aplicar técnicas de anonimización adicionales"
            )
            recomendaciones.append(
                "🎲 Aumentar ruido en CTGAN (reducir epochs o learning_rate)"
            )
        
        # Detección de sintéticos alta (fáciles de distinguir)
        if metricas_detalladas.get("deteccion_sinteticos", 1) < 0.5:
            recomendaciones.append(
                "🎭 Los datos sintéticos son muy distinguibles de los reales"
            )
            recomendaciones.append(
                "⚙️ Ajustar discriminator_steps y learning_rate del generador"
            )
        
        # Si todo está bien
        if not recomendaciones:
            recomendaciones.append(
                "✅ Calidad de datos sintéticos es aceptable para uso en entrenamiento"
            )
        
        return recomendaciones
    
    def guardar_modelo(self, ruta: str) -> bool:
        """Guarda el modelo CTGAN entrenado"""
        if not self.entrenado or self.modelo_ctgan is None:
            logger.error("❌ No hay modelo entrenado para guardar")
            return False
        
        try:
            self.modelo_ctgan.save(filepath=ruta)
            logger.info(f"✅ Modelo CTGAN guardado en: {ruta}")
            return True
        except Exception as error:
            logger.error(f"❌ Error guardando modelo: {error}")
            return False
    
    def cargar_modelo(self, ruta: str) -> bool:
        """Carga un modelo CTGAN previamente entrenado"""
        try:
            self.modelo_ctgan = CTGANSynthesizer.load(filepath=ruta)
            self.entrenado = True
            logger.info(f"✅ Modelo CTGAN cargado desde: {ruta}")
            return True
        except Exception as error:
            logger.error(f"❌ Error cargando modelo: {error}")
            return False