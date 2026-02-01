# nucleo/generador_sintetico.py -
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
# Módulo: enerador_sintetico.py 
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
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.evaluation.single_table import evaluate_quality
from sdv.metrics.tabular import (
    KSComplement,
    CSTest,
    LogisticDetection,
    CorrelationSimilarity
)

logger = logging.getLogger(__name__)


class GeneradorSintetico:
    """Generador de datos sinteticos usando CTGAN"""

    def __init__(self):
        self.modelo_ctgan = None
        self.entrenado = False
        self.metadata = None
        self.scaler = StandardScaler()
        self.datos_entrenamiento_escalados = None

    def entrenar_ctgan(
        self,
        datos_reales: pd.DataFrame,
        variables_discretas: List[str] = None,
        epocas: int = 300
    ) -> Dict:
        """Entrena CTGAN usando SDV y metadata"""
        try:
            logger.info(
                f"Entrenando CTGAN con {len(datos_reales)} muestras"
            )

            self.metadata = SingleTableMetadata()
            self.metadata.detect_from_dataframe(datos_reales)

            if variables_discretas:
                for var in variables_discretas:
                    if var in datos_reales.columns:
                        self.metadata.update_column(
                            column_name=var,
                            sdtype="categorical"
                        )

            self.modelo_ctgan = CTGANSynthesizer(
                metadata=self.metadata,
                epochs=epocas,
                verbose=True,
                enforce_min_max_values=True,
                enforce_rounding=True,
                generator_dim=(256, 256),
                discriminator_dim=(256, 256),
                batch_size=500,
                discriminator_steps=1,
                log_frequency=True
            )

            datos_numericos = datos_reales.select_dtypes(
                include=[np.number]
            )
            if len(datos_numericos.columns) > 0:
                self.datos_entrenamiento_escalados = (
                    self.scaler.fit_transform(datos_numericos)
                )

            logger.info("Iniciando entrenamiento del CTGAN")
            self.modelo_ctgan.fit(datos_reales)

            self.entrenado = True
            logger.info("CTGAN entrenado correctamente")

            return {
                "estado": "exito",
                "muestras_entrenamiento": len(datos_reales),
                "epocas": epocas,
                "dimension_sintetica": datos_reales.shape[1],
                "variables_categoricas": (
                    len(variables_discretas)
                    if variables_discretas else 0
                ),
                "metadata": self.metadata.to_dict()
            }

        except Exception as error:
            logger.error(f"Error entrenando CTGAN: {error}")
            return {"estado": "error", "error": str(error)}

    def generar_datos_sinteticos(
        self,
        cantidad_muestras: int,
        variables_condicionales: Dict = None
    ) -> pd.DataFrame:
        """Genera datos sinteticos usando CTGAN entrenado"""
        if not self.entrenado or self.modelo_ctgan is None:
            raise ValueError(
                "CTGAN no esta entrenado. "
                "Ejecute entrenar_ctgan primero."
            )

        if cantidad_muestras <= 0:
            raise ValueError(
                f"cantidad_muestras invalida: {cantidad_muestras}"
            )

        try:
            logger.info(
                f"Generando {cantidad_muestras} muestras sinteticas"
            )

            muestras = self.modelo_ctgan.sample(
                num_rows=cantidad_muestras
            )

            if variables_condicionales:
                muestras = self._aplicar_condiciones(
                    muestras, variables_condicionales
                )

            logger.info(
                f"Muestras sinteticas generadas: {len(muestras)}"
            )
            return muestras

        except Exception as error:
            logger.error(
                f"Error generando datos sinteticos: {error}"
            )
            raise

    def _aplicar_condiciones(
        self,
        datos: pd.DataFrame,
        condiciones: Dict
    ) -> pd.DataFrame:
        datos_filtrados = datos.copy()

        for variable, valor in condiciones.items():
            if variable not in datos.columns:
                logger.warning(
                    f"Variable no existe: {variable}"
                )
                continue

            if isinstance(valor, (list, tuple)):
                datos_filtrados = datos_filtrados[
                    datos_filtrados[variable].isin(valor)
                ]
            else:
                datos_filtrados[variable] = valor

        if len(datos_filtrados) == 0:
            logger.warning(
                "Condiciones demasiado restrictivas"
            )
            return datos

        return datos_filtrados

    def evaluar_calidad_sinteticos(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> Dict:
        """Evalua calidad y privacidad de datos sinteticos"""
        try:
            logger.info(
                "Evaluando calidad de datos sinteticos"
            )

            quality_report = evaluate_quality(
                real_data=datos_reales,
                synthetic_data=datos_sinteticos,
                metadata=self.metadata
            )

            puntaje_sdv = quality_report.get_score()

            metricas = self._calcular_metricas_detalladas(
                datos_reales, datos_sinteticos
            )

            riesgo = self._calcular_riesgo_privacidad_real(
                datos_reales, datos_sinteticos
            )

            cumple = (
                puntaje_sdv > 0.7 and
                riesgo < 0.1 and
                metricas["similitud_estadistica"] > 0.7
            )

            return {
                "puntaje_calidad_sdv": float(puntaje_sdv),
                "riesgo_privacidad": riesgo,
                "cumple_estandares": cumple,
                "metricas": metricas
            }

        except Exception as error:
            logger.error(
                f"Error evaluando calidad: {error}"
            )
            return {
                "puntaje_calidad_sdv": 0.0,
                "riesgo_privacidad": 1.0,
                "cumple_estandares": False,
                "error": str(error)
            }
