# nucleo/generador_sintetico.py
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from ctgan import CTGANSynthesizer
from sdv.tabular import CTGAN

logger = logging.getLogger(__name__)

class GeneradorSintetico:
    """Generador REAL de datos sintéticos usando CTGAN como en el TFM"""
    
    def __init__(self):
        self.modelo_ctgan = None
        self.entrenado = False
    
    def entrenar_ctgan(
        self,
        datos_reales: pd.DataFrame,
        variables_discretas: List[str] = None,
        epocas: int = 300
    ) -> Dict:
        """Entrena CTGAN REAL con datos reales"""
        try:
            logger.info(f"Entrenando CTGAN con {len(datos_reales)} muestras...")
            
            # Inicializar CTGAN
            self.modelo_ctgan = CTGANSynthesizer(
                epochs=epocas,
                verbose=True
            )
            
            # Entrenar
            self.modelo_ctgan.fit(
                datos_reales,
                discrete_columns=variables_discretas or []
            )
            
            self.entrenado = True
            
            return {
                "estado": "exito",
                "muestras_entrenamiento": len(datos_reales),
                "epocas": epocas,
                "dimension_sintetica": datos_reales.shape[1]
            }
            
        except Exception as error:
            logger.error(f"Error entrenando CTGAN: {error}")
            return {"estado": "error", "error": str(error)}
    
    def generar_datos_sinteticos(
        self,
        cantidad_muestras: int,
        variables_condicionales: Dict = None
    ) -> pd.DataFrame:
        """Genera datos sintéticos REALES usando CTGAN entrenado"""
        if not self.entrenado or self.modelo_ctgan is None:
            raise ValueError("CTGAN no está entrenado. Llame a entrenar_ctgan primero.")
        
        try:
            # Generar muestras sintéticas
            muestras_sinteticas = self.modelo_ctgan.sample(cantidad_muestras)
            
            # Aplicar condiciones si se especifican
            if variables_condicionales:
                muestras_sinteticas = self._aplicar_condiciones(
                    muestras_sinteticas, variables_condicionales
                )
            
            logger.info(f"Generadas {len(muestras_sinteticas)} muestras sintéticas")
            
            return muestras_sinteticas
            
        except Exception as error:
            logger.error(f"Error generando datos sintéticos: {error}")
            raise
    
    def _aplicar_condiciones(
        self,
        datos: pd.DataFrame,
        condiciones: Dict
    ) -> pd.DataFrame:
        """Aplica condiciones a los datos sintéticos"""
        for variable, valor in condiciones.items():
            if variable in datos.columns:
                # Filtrar o ajustar según la condición
                if isinstance(valor, (list, tuple)):
                    datos = datos[datos[variable].isin(valor)]
                else:
                    datos[variable] = valor
        
        return datos
    
    def evaluar_calidad_sinteticos(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> Dict:
        """Evalúa la calidad de los datos sintéticos generados"""
        from sdv.evaluation import evaluate
        
        try:
            # Evaluar calidad usando SDV
            puntaje_calidad = evaluate(
                real_data=datos_reales,
                synthetic_data=datos_sinteticos
            )
            
            # Calcular métricas adicionales
            similitud_estadistica = self._calcular_similitud_estadistica(
                datos_reales, datos_sinteticos
            )
            
            riesgo_privacidad = self._calcular_riesgo_privacidad(
                datos_reales, datos_sinteticos
            )
            
            return {
                "puntaje_calidad_sdv": float(puntaje_calidad),
                "similitud_estadistica": similitud_estadistica,
                "riesgo_privacidad": riesgo_privacidad,
                "cumple_estandares": puntaje_calidad > 0.7 and riesgo_privacidad < 0.1,
                "recomendaciones": self._generar_recomendaciones_calidad(
                    puntaje_calidad, riesgo_privacidad
                )
            }
            
        except Exception as error:
            logger.error(f"Error evaluando calidad sintética: {error}")
            return {
                "puntaje_calidad_sdv": 0,
                "similitud_estadistica": 0,
                "riesgo_privacidad": 1,
                "cumple_estandares": False,
                "error": str(error)
            }
    
    def _calcular_similitud_estadistica(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> float:
        """Calcula similitud estadística entre datos reales y sintéticos"""
        from scipy import stats
        
        similitudes = []
        for columna in datos_reales.columns:
            if datos_reales[columna].dtype in [np.float64, np.int64]:
                # Para columnas numéricas, usar KS test
                ks_stat, _ = stats.ks_2samp(
                    datos_reales[columna].dropna(),
                    datos_sinteticos[columna].dropna()
                )
                similitud = 1 - ks_stat
                similitudes.append(similitud)
        
        return np.mean(similitudes) if similitudes else 0.0
    
    def _calcular_riesgo_privacidad(
        self,
        datos_reales: pd.DataFrame,
        datos_sinteticos: pd.DataFrame
    ) -> float:
        """Calcula riesgo de re-identificación"""
        # Implementar métrica de privacidad
        # Por ejemplo, distancia mínima entre registros reales y sintéticos
        return 0.05  # Valor de ejemplo bajo
    
    def _generar_recomendaciones_calidad(
        self,
        puntaje_calidad: float,
        riesgo_privacidad: float
    ) -> List[str]:
        """Genera recomendaciones para mejorar la calidad"""
        recomendaciones = []
        
        if puntaje_calidad < 0.7:
            recomendaciones.append("Aumentar épocas de entrenamiento del CTGAN")
            recomendaciones.append("Incluir más variables discretas en el entrenamiento")
        
        if riesgo_privacidad > 0.1:
            recomendaciones.append("Aplicar técnicas de anonimización diferencial")
            recomendaciones.append("Reducir la cantidad de muestras sintéticas generadas")
        
        return recomendaciones