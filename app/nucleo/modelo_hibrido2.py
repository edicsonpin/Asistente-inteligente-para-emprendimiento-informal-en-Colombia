# nucleo/modelo_hibrido.py - VERSIÓN CORREGIDA

import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
import os
from pathlib import Path

# Librerías REALES como en el TFM
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
        self.id_modelo = 1
        self.version = "1.0.0"
        self.nombre_modelo_embedding = "red_neuronal_embeddings_tfm"
        self.modelos_cargados = False  # ✅ NUEVO: Flag de estado
    
    def cargar_modelos(self):
        """
        ✅ CORRECCIÓN 1 y 2: Carga los modelos con validación robusta
        """
        try:
            logger.info(f"📦 Cargando modelos desde: {self.ruta_modelos}")
            
            # ✅ Verificar que el directorio existe
            if not os.path.exists(self.ruta_modelos):
                raise FileNotFoundError(
                    f"Directorio de modelos no encontrado: {self.ruta_modelos}"
                )
            
            # 1. Cargar modelo LightGBM
            ruta_lgb = os.path.join(self.ruta_modelos, "lightgbm_model.txt")
            if not os.path.exists(ruta_lgb):
                raise FileNotFoundError(
                    f"Modelo LightGBM no encontrado en: {ruta_lgb}\n"
                    f"Asegúrese de que el modelo ha sido entrenado correctamente."
                )
            
            logger.info("   Cargando modelo LightGBM...")
            self.modelo_lightgbm = lgb.Booster(model_file=ruta_lgb)
            
            if self.modelo_lightgbm is None:
                raise ValueError("Modelo LightGBM no se cargó correctamente")
            
            num_arboles = self.modelo_lightgbm.num_trees()
            logger.info(f"   ✅ LightGBM cargado: {num_arboles} árboles")
            
            # 2. Cargar modelo de embeddings (Red Neuronal)
            ruta_nn = os.path.join(self.ruta_modelos, "red_neuronal_embeddings.h5")
            if not os.path.exists(ruta_nn):
                raise FileNotFoundError(
                    f"Red neuronal no encontrada en: {ruta_nn}\n"
                    f"Asegúrese de que el modelo ha sido entrenado correctamente."
                )
            
            logger.info("   Cargando red neuronal de embeddings...")
            self.modelo_embedding = keras.models.load_model(
                ruta_nn,
                compile=False  # ✅ No necesitamos compilar para inferencia
            )
            
            if self.modelo_embedding is None:
                raise ValueError("Red neuronal no se cargó correctamente")
            
            num_parametros = self.modelo_embedding.count_params()
            logger.info(f"   ✅ Red neuronal cargada: {num_parametros:,} parámetros")
            
            # 3. Cargar preprocesador
            ruta_preprocesador = os.path.join(self.ruta_modelos, "preprocesador.pkl")
            if not os.path.exists(ruta_preprocesador):
                raise FileNotFoundError(
                    f"Preprocesador no encontrado en: {ruta_preprocesador}"
                )
            
            logger.info("   Cargando preprocesador...")
            with open(ruta_preprocesador, 'rb') as f:
                self.preprocesador = pickle.load(f)
            
            # ✅ CORRECCIÓN 5: Validar estructura del preprocesador
            campos_requeridos = [
                "nombres_caracteristicas",
                "nombres_clases",
                "codificador_clases",
                "orden_caracteristicas_numericas",
                "orden_embeddings"
            ]
            
            for campo in campos_requeridos:
                if campo not in self.preprocesador:
                    logger.warning(
                        f"⚠️ Campo '{campo}' faltante en preprocesador, "
                        f"inicializando con valor por defecto"
                    )
                    self.preprocesador[campo] = self._obtener_valor_por_defecto(campo)
            
            logger.info("   ✅ Preprocesador cargado")
            
            # 4. Inicializar explicadores SHAP y LIME
            logger.info("   Inicializando explicadores XAI...")
            self._inicializar_explicadores()
            
            self.modelos_cargados = True
            logger.info("✅ Modelo híbrido cargado exitosamente")
            
        except FileNotFoundError as error:
            logger.error(f"❌ Archivo no encontrado: {error}")
            raise
        except Exception as error:
            logger.error(f"❌ Error cargando modelo híbrido: {error}")
            raise
    
    def _obtener_valor_por_defecto(self, campo: str):
        """✅ NUEVO: Obtiene valores por defecto para campos faltantes"""
        valores_defecto = {
            "nombres_caracteristicas": [],
            "nombres_clases": ["MUY_BAJO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"],
            "codificador_clases": None,
            "orden_caracteristicas_numericas": [],
            "orden_embeddings": [],
            "escalador": None,
            "codificadores_categoricos": {}
        }
        return valores_defecto.get(campo)
    
    def _inicializar_explicadores(self):
        """
        ✅ CORRECCIÓN 4: Inicializa los explicadores SHAP y LIME con manejo robusto
        """
        # SHAP es crítico - debe funcionar
        try:
            if self.modelo_lightgbm is None:
                raise ValueError(
                    "Modelo LightGBM debe estar cargado antes de inicializar SHAP"
                )
            
            self.explicador_shap = shap.TreeExplainer(self.modelo_lightgbm)
            logger.info("   ✅ Explicador SHAP inicializado")
            
        except Exception as error:
            logger.error(f"   ❌ Error crítico inicializando SHAP: {error}")
            raise
        
        # LIME es opcional pero útil
        try:
            ruta_datos = os.path.join(self.ruta_modelos, "datos_entrenamiento.pkl")
            
            if os.path.exists(ruta_datos):
                with open(ruta_datos, 'rb') as f:
                    datos_entrenamiento = pickle.load(f)
                
                # Validar que los datos tienen la forma correcta
                if not isinstance(datos_entrenamiento, np.ndarray):
                    raise TypeError(
                        f"datos_entrenamiento debe ser np.ndarray, "
                        f"recibido: {type(datos_entrenamiento)}"
                    )
                
                if len(datos_entrenamiento.shape) != 2:
                    raise ValueError(
                        f"datos_entrenamiento debe ser 2D, "
                        f"recibido shape: {datos_entrenamiento.shape}"
                    )
                
                self.explicador_lime = lime.lime_tabular.LimeTabularExplainer(
                    datos_entrenamiento,
                    feature_names=self.preprocesador.get(
                        "nombres_caracteristicas_completas",
                        self.preprocesador.get("nombres_caracteristicas", [])
                    ),
                    class_names=self.preprocesador.get("nombres_clases", []),
                    mode='classification',
                    discretize_continuous=True,
                    random_state=42
                )
                logger.info("   ✅ Explicador LIME inicializado")
            else:
                logger.warning(
                    f"   ⚠️ Datos de entrenamiento no encontrados en: {ruta_datos}"
                )
                logger.warning("   ⚠️ LIME no estará disponible")
                self.explicador_lime = None
        
        except Exception as error:
            logger.error(f"   ❌ Error inicializando LIME: {error}")
            logger.warning("   ⚠️ Continuando sin LIME")
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
        if not self.modelos_cargados:
            raise ValueError(
                "Modelos no cargados. Llame a cargar_modelos() primero."
            )
        
        try:
            # 1. Preprocesar características numéricas
            caracteristicas_procesadas = self._preprocesar_caracteristicas(
                caracteristicas_numericas
            )
            
            # 2. Concatenar con embeddings
            vector_entrada = self._construir_vector_entrada(
                caracteristicas_procesadas,
                embeddings_categoricos.get("embedding_concatenado", [])
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
            
            # 5. Obtener categoría de riesgo
            if self.preprocesador.get("codificador_clases"):
                categoria_riesgo = self.preprocesador["codificador_clases"].inverse_transform(
                    [categoria_idx]
                )[0]
            else:
                categorias = self.preprocesador.get(
                    "nombres_clases",
                    ["MUY_BAJO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
                )
                categoria_riesgo = categorias[categoria_idx] if categoria_idx < len(categorias) else "DESCONOCIDA"
            
            # 6. Generar explicaciones SHAP y LIME REALES
            explicaciones = self._generar_explicaciones_prediccion(
                vector_entrada, caracteristicas_numericas
            )
            
            return {
                "categoria_riesgo": categoria_riesgo,
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
                "tiempo_procesamiento_ms": 0
            }
            
        except Exception as error:
            logger.error(f"❌ Error en predicción: {error}")
            raise
    
    def predecir_riesgo_simple(self, caracteristicas: Dict) -> Dict:
        """
        ✅ CORRECCIÓN 3: Versión simplificada para uso en optimización de contrafactuales
        
        Acepta dict plano sin separar embeddings
        """
        if not self.modelos_cargados:
            raise ValueError("Modelos no cargados. Llame a cargar_modelos() primero.")
        
        try:
            # Separar características numéricas de categóricas
            caracteristicas_num = {}
            caracteristicas_cat = {}
            
            for nombre, valor in caracteristicas.items():
                if isinstance(valor, (int, float, np.integer, np.floating)):
                    caracteristicas_num[nombre] = valor
                else:
                    caracteristicas_cat[nombre] = valor
            
            # Generar embeddings para categóricas
            embeddings_individuales = {}
            for cat in self.preprocesador.get("columnas_categoricas", []):
                if cat in caracteristicas_cat:
                    try:
                        emb = self.generar_embedding_categorico(
                            cat, caracteristicas_cat[cat]
                        )
                        embeddings_individuales[cat] = emb
                    except Exception as e:
                        logger.warning(f"Error generando embedding para {cat}: {e}")
            
            # Construir dict de embeddings
            embeddings_dict = {
                "embedding_concatenado": self.concatenar_embeddings(embeddings_individuales),
                "embeddings_individuales": embeddings_individuales
            }
            
            # Llamar a predicción completa
            return self.predecir_riesgo(caracteristicas_num, embeddings_dict)
            
        except Exception as error:
            logger.error(f"❌ Error en predicción simple: {error}")
            # Retornar predicción por defecto en caso de error
            return {
                "categoria_riesgo": "MEDIO",
                "puntaje_riesgo": 50.0,
                "confianza_prediccion": 0.2,
                "probabilidades": {
                    "MUY_BAJO": 0.2,
                    "BAJO": 0.2,
                    "MEDIO": 0.2,
                    "ALTO": 0.2,
                    "MUY_ALTO": 0.2
                },
                "error": str(error)
            }
    
    def generar_embedding_categorico(
        self,
        categoria: str,
        valor: str
    ) -> List[float]:
        """Genera embedding REAL para una categoría usando la red neuronal"""
        try:
            # Codificar la categoría
            if categoria in self.preprocesador.get("codificadores_categoricos", {}):
                codificador = self.preprocesador["codificadores_categoricos"][categoria]
                
                # Validar que el valor existe en el codificador
                if hasattr(codificador, 'classes_'):
                    if valor not in codificador.classes_:
                        logger.warning(
                            f"Valor '{valor}' no reconocido para '{categoria}', "
                            f"usando valor por defecto"
                        )
                        valor = codificador.classes_[0]
                
                valor_codificado = codificador.transform([valor])[0]
            else:
                logger.warning(f"Codificador no encontrado para '{categoria}'")
                valor_codificado = 0
            
            # Generar embedding
            entrada = np.array([[valor_codificado]])
            embedding = self.modelo_embedding.predict(entrada, verbose=0)[0]
            
            return embedding.tolist()
            
        except Exception as error:
            logger.error(f"Error generando embedding para {categoria}: {error}")
            # Retornar embedding por defecto
            return [0.0] * 32  # Asumiendo dimensión 32
    
    def concatenar_embeddings(self, embeddings_individuales: Dict) -> List[float]:
        """Concatena embeddings individuales en un vector único"""
        vector_concatenado = []
        
        orden = self.preprocesador.get("orden_embeddings", [])
        if not orden:
            # Si no hay orden definido, usar orden alfabético
            orden = sorted(embeddings_individuales.keys())
        
        for categoria in orden:
            if categoria in embeddings_individuales:
                embedding = embeddings_individuales[categoria]
                if isinstance(embedding, list):
                    vector_concatenado.extend(embedding)
                elif isinstance(embedding, np.ndarray):
                    vector_concatenado.extend(embedding.tolist())
        
        return vector_concatenado
    
    def _preprocesar_caracteristicas(self, caracteristicas: Dict) -> np.ndarray:
        """Preprocesa características numéricas"""
        # Convertir a array en el orden correcto
        orden = self.preprocesador.get("orden_caracteristicas_numericas", [])
        if not orden:
            orden = sorted(caracteristicas.keys())
        
        valores_ordenados = []
        for nombre in orden:
            if nombre in caracteristicas:
                valores_ordenados.append(caracteristicas[nombre])
            else:
                valores_ordenados.append(0.0)
        
        # Estandarizar
        valores_array = np.array(valores_ordenados).reshape(1, -1)
        escalador = self.preprocesador.get("escalador")
        if escalador:
            valores_array = escalador.transform(valores_array)
        
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
        pesos = np.array([10, 30, 50, 70, 90])
        
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
        try:
            # Calcular valores SHAP
            shap_values = self.explicador_shap.shap_values(vector_entrada)
            
            # Obtener nombres de características
            nombres_caracteristicas = self.preprocesador.get(
                "nombres_caracteristicas_completas",
                self.preprocesador.get("nombres_caracteristicas", [])
            )
            
            # Formatear resultados
            valores_shap = {}
            for i, nombre in enumerate(nombres_caracteristicas):
                if i < len(shap_values[0]):
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
            
        except Exception as error:
            logger.error(f"Error generando SHAP: {error}")
            return {"disponible": False, "error": str(error)}
    
    def _generar_lime_real(
        self,
        vector_entrada: np.ndarray,
        caracteristicas_originales: Dict
    ) -> Dict:
        """Genera explicación LIME REAL"""
        if not self.explicador_lime:
            return {
                "disponible": False,
                "razon": "Explicador LIME no inicializado"
            }
        
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
                caracteristicas_lime.append({
                    "caracteristica": feature,
                    "peso": weight,
                    "interpretacion": "FAVORABLE" if weight < 0 else "DESFAVORABLE"
                })
            
            return {
                "disponible": True,
                "caracteristicas_locales": caracteristicas_lime,
                "puntaje_local": explicacion.score
            }
            
        except Exception as error:
            logger.error(f"Error generando LIME: {error}")
            return {"disponible": False, "error": str(error)}
    
    def _funcion_predict_proba(self, instancias: np.ndarray) -> np.ndarray:
        """Función de predicción para LIME"""
        return self.modelo_lightgbm.predict(instancias)