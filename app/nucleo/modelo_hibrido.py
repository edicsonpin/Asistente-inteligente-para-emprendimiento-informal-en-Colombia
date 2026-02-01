# nucleo/modelo_hibrido.py
import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

# Librerías REALES como en el TFMl
import lightgbm as lgb
import tensorflow as tf
from tensorflow import keras
import shap
import lime
import lime.lime_tabular


logger = logging.getLogger(__name__)

class ModeloHibridoTFM:
    """Implementación REAL del modelo híbrido LightGBM + Red Neuronal del TFM"""
    
    def __init__(self, ruta_modelos: str = "modelos/hibrido_tfm"):
        self.ruta_modelos = ruta_modelos
        self.modelo_lightgbm = None
        self.modelo_embedding = None
        self.explicador_shap = None
        self.explicador_lime = None
        self.preprocesador = None
        self.id_modelo = 1  # ID en base de datos
        self.version = "1.0.0"
        self.nombre_modelo_embedding = "red_neuronal_embeddings_tfm"
        
    def cargar_modelos(self):
        """Carga los modelos entrenados desde archivos"""
        try:
            # 1. Cargar modelo LightGBM
            ruta_lgb = f"{self.ruta_modelos}/lightgbm_model.txt"
            self.modelo_lightgbm = lgb.Booster(model_file=ruta_lgb)
            
            # 2. Cargar modelo de embeddings (Red Neuronal)
            ruta_nn = f"{self.ruta_modelos}/red_neuronal_embeddings.h5"
            self.modelo_embedding = keras.models.load_model(ruta_nn)
            
            # 3. Cargar preprocesador
            with open(f"{self.ruta_modelos}/preprocesador.pkl", 'rb') as f:
                self.preprocesador = pickle.load(f)
            
            # 4. Inicializar explicadores SHAP y LIME
            self._inicializar_explicadores()
            
            logger.info("Modelo híbrido cargado exitosamente")
            
        except Exception as error:
            logger.error(f"Error cargando modelo híbrido: {error}")
            raise
    
    def _inicializar_explicadores(self):
        """Inicializa los explicadores SHAP y LIME REALES"""
        # SHAP para explicaciones globales
        self.explicador_shap = shap.TreeExplainer(self.modelo_lightgbm)
        
        # LIME para explicaciones locales
        # Necesitamos datos de entrenamiento para LIME
        try:
            with open(f"{self.ruta_modelos}/datos_entrenamiento.pkl", 'rb') as f:
                datos_entrenamiento = pickle.load(f)
            
            self.explicador_lime = lime.lime_tabular.LimeTabularExplainer(
                datos_entrenamiento,
                feature_names=self.preprocesador["nombres_caracteristicas"],
                class_names=self.preprocesador["nombres_clases"],
                mode='classification'
            )
        except:
            logger.warning("No se pudieron cargar datos para LIME, inicializando sin ellos")
            self.explicador_lime = None
    
    def predecir_riesgo(
        self,
        caracteristicas_numericas: Dict,
        embeddings_categoricos: Dict
    ) -> Dict:
        """
        Predice riesgo usando el modelo híbrido REAL
        
        Returns:
            Dict con categoría de riesgo, puntaje, probabilidades y explicaciones
        """
        # 1. Preprocesar características numéricas
        caracteristicas_procesadas = self._preprocesar_caracteristicas(
            caracteristicas_numericas
        )
        
        # 2. Concatenar con embeddings
        vector_entrada = self._construir_vector_entrada(
            caracteristicas_procesadas,
            embeddings_categoricos["embedding_concatenado"]
        )
        
        # 3. Predecir con LightGBM
        prediccion_lgb = self.modelo_lightgbm.predict(
            vector_entrada.reshape(1, -1),
            num_iteration=self.modelo_lightgbm.best_iteration
        )
        
        # 4. Interpretar resultados
        probabilidades = prediccion_lgb[0]
        categoria_idx = np.argmax(probabilidades)
        puntaje_riesgo = self._calcular_puntaje_riesgo(probabilidades)
        
        # 5. Generar explicaciones SHAP y LIME REALES
        explicaciones = self._generar_explicaciones_prediccion(
            vector_entrada, caracteristicas_numericas
        )
        
        return {
            "categoria_riesgo": self.preprocesador["codificador_clases"].inverse_transform([categoria_idx])[0],
            "puntaje_riesgo": puntaje_riesgo,
            "confianza_prediccion": float(probabilidades[categoria_idx]),
            "probabilidades": {
                "MUY_BAJO": float(probabilidades[0]),
                "BAJO": float(probabilidades[1]),
                "MEDIO": float(probabilidades[2]),
                "ALTO": float(probabilidades[3]),
                "MUY_ALTO": float(probabilidades[4])
            },
            "caracteristicas_importantes": explicaciones["shap"]["top_caracteristicas"],
            "impacto_caracteristicas": explicaciones["shap"]["valores"],
            "explicacion_lime": explicaciones["lime"],
            "tiempo_procesamiento_ms": 0  # Se calcularía con time.time()
        }
    
    def generar_embedding_categorico(
        self,
        categoria: str,
        valor: str
    ) -> List[float]:
        """Genera embedding REAL para una categoría usando la red neuronal"""
        # Codificar la categoría
        if categoria in self.preprocesador["codificadores_categoricos"]:
            codificador = self.preprocesador["codificadores_categoricos"][categoria]
            valor_codificado = codificador.transform([valor])[0]
        else:
            valor_codificado = 0
        
        # Generar embedding
        entrada = np.array([[valor_codificado]])
        embedding = self.modelo_embedding.predict(entrada)[0]
        
        return embedding.tolist()
    
    def concatenar_embeddings(self, embeddings_individuales: Dict) -> List[float]:
        """Concatena embeddings individuales en un vector único"""
        vector_concatenado = []
        for categoria in self.preprocesador["orden_embeddings"]:
            if categoria in embeddings_individuales:
                vector_concatenado.extend(embeddings_individuales[categoria])
        
        return vector_concatenado
    
    def _preprocesar_caracteristicas(self, caracteristicas: Dict) -> np.ndarray:
        """Preprocesa características numéricas"""
        # Convertir a array en el orden correcto
        valores_ordenados = []
        for nombre in self.preprocesador["orden_caracteristicas_numericas"]:
            if nombre in caracteristicas:
                valores_ordenados.append(caracteristicas[nombre])
            else:
                valores_ordenados.append(0.0)  # Valor por defecto
        
        # Estandarizar
        valores_array = np.array(valores_ordenados).reshape(1, -1)
        if self.preprocesador["escalador"]:
            valores_array = self.preprocesador["escalador"].transform(valores_array)
        
        return valores_array
    
    def _construir_vector_entrada(
        self,
        caracteristicas_numericas: np.ndarray,
        embedding_concatenado: List[float]
    ) -> np.ndarray:
        """Construye el vector de entrada para LightGBM"""
        # Convertir embedding a array
        embedding_array = np.array(embedding_concatenado).reshape(1, -1)
        
        # Concatenar características numéricas con embeddings
        vector_completo = np.concatenate(
            [caracteristicas_numericas, embedding_array],
            axis=1
        )
        
        return vector_completo
    
    def _calcular_puntaje_riesgo(self, probabilidades: np.ndarray) -> float:
        """Calcula puntaje de riesgo numérico (0-100)"""
        # Pesos para cada categoría
        pesos = np.array([10, 30, 50, 70, 90])  # MUY_BAJO a MUY_ALTO
        
        # Puntaje ponderado
        puntaje = np.sum(probabilidades * pesos)
        
        return float(puntaje)
    
    def _generar_explicaciones_prediccion(
        self,
        vector_entrada: np.ndarray,
        caracteristicas_originales: Dict
    ) -> Dict:
        """Genera explicaciones SHAP y LIME REALES"""
        explicaciones = {
            "shap": self._generar_shap_real(vector_entrada),
            "lime": self._generar_lime_real(vector_entrada, caracteristicas_originales)
        }
        
        return explicaciones
    
    def _generar_shap_real(self, vector_entrada: np.ndarray) -> Dict:
        """Genera valores SHAP REALES"""
        # Calcular valores SHAP
        shap_values = self.explicador_shap.shap_values(vector_entrada)
        
        # Obtener nombres de características
        nombres_caracteristicas = self.preprocesador["nombres_caracteristicas_completas"]
        
        # Formatear resultados
        valores_shap = {}
        for i, nombre in enumerate(nombres_caracteristicas):
            if i < len(shap_values[0]):  # Asegurar que existe
                valores_shap[nombre] = float(shap_values[0][i])
        
        # Ordenar por importancia absoluta
        caracteristicas_ordenadas = sorted(
            valores_shap.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        top_caracteristicas = [
            {
                "nombre": nombre,
                "valor_shap": valor,
                "impacto": "REDUCE_RIESGO" if valor < 0 else "AUMENTA_RIESGO"
            }
            for nombre, valor in caracteristicas_ordenadas[:5]
        ]
        
        return {
            "valores": valores_shap,
            "valor_esperado": float(self.explicador_shap.expected_value[0]),
            "top_caracteristicas": top_caracteristicas
        }
    
    def _generar_lime_real(
        self,
        vector_entrada: np.ndarray,
        caracteristicas_originales: Dict
    ) -> Dict:
        """Genera explicación LIME REAL"""
        if not self.explicador_lime:
            return {"disponible": False, "razon": "Explicador no inicializado"}
        
        try:
            # Generar explicación LIME
            explicacion = self.explicador_lime.explain_instance(
                vector_entrada[0],
                self._funcion_predict_proba,
                num_features=5
            )
            
            # Formatear resultados
            caracteristicas_lime = []
            for feature, weight in explicacion.as_list():
                # Extraer nombre de característica y valor
                caracteristicas_lime.append({
                    "caracteristica": feature.split(' ') if ' ' in feature else feature,
                    "peso": weight,
                    "interpretacion": "FAVORABLE" if weight < 0 else "DESFAVORABLE"
                })
            
            return {
                "disponible": True,
                "caracteristicas_locales": caracteristicas_lime,
                "puntaje_local": explicacion.score,
                "explicacion_texto": str(explicacion)
            }
            
        except Exception as error:
            logger.error(f"Error generando LIME: {error}")
            return {"disponible": False, "error": str(error)}
    
    def _funcion_predict_proba(self, instancias: np.ndarray) -> np.ndarray:
        """Función de predicción para LIME"""
        return self.modelo_lightgbm.predict(instancias)