import numpy as np
import lightgbm as lgb
from typing import Dict, List, Tuple
import time
from datetime import datetime

from nucleo.excepciones import ModeloNoDisponibleExcepcion

class ServicioModelo:
    
    def __init__(self):
        self.modelo_lightgbm = None
        self.modelo_embedding = None
        self.caracteristicas_modelo = None
        self.umbral_confianza = 0.7
        self.cargado = False
    
    def cargar_modelo(self, ruta_modelo: str = None):
        try:
            if ruta_modelo:
                self.modelo_lightgbm = lgb.Booster(model_file=ruta_modelo)
            else:
                self.modelo_lightgbm = self._crear_modelo_demo()
            
            self.caracteristicas_modelo = [
                "experiencia_sector",
                "meses_operacion",
                "empleados_directos",
                "ingresos_mensuales_promedio",
                "capital_trabajo",
                "nivel_educacion_cod",
                "sector_negocio_cod",
                "ciudad_cod"
            ]
            
            self.cargado = True
            
        except Exception as error:
            raise ModeloNoDisponibleExcepcion(
                f"Error al cargar modelo: {str(error)}"
            )
    
    def _crear_modelo_demo(self):
        parametros = {
            'objective': 'multiclass',
            'num_class': 5,
            'metric': 'multi_logloss',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9
        }
        
        datos_entrenamiento = lgb.Dataset(
            np.random.rand(100, 8),
            label=np.random.randint(0, 5, 100)
        )
        
        modelo = lgb.train(
            parametros,
            datos_entrenamiento,
            num_boost_round=100
        )
        
        return modelo
    
    def predecir_riesgo(self, caracteristicas: Dict) -> Dict:
        if not self.cargado:
            raise ModeloNoDisponibleExcepcion("Modelo no cargado")
        
        tiempo_inicio = time.time()
        
        vector_caracteristicas = self._preparar_caracteristicas(caracteristicas)
        
        probabilidades = self.modelo_lightgbm.predict(vector_caracteristicas)[0]
        
        categorias = ["MUY_BAJO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
        categoria_predicha = categorias[np.argmax(probabilidades)]
        
        puntaje_riesgo = self._calcular_puntaje_riesgo(probabilidades)
        
        confianza = float(np.max(probabilidades))
        
        tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
        
        return {
            "categoria_riesgo": categoria_predicha,
            "puntaje_riesgo": puntaje_riesgo,
            "confianza_prediccion": round(confianza, 4),
            "probabilidades": {
                "MUY_BAJO": round(float(probabilidades[0]), 4),
                "BAJO": round(float(probabilidades[1]), 4),
                "MEDIO": round(float(probabilidades[2]), 4),
                "ALTO": round(float(probabilidades[3]), 4),
                "MUY_ALTO": round(float(probabilidades[4]), 4)
            },
            "tiempo_procesamiento_ms": round(tiempo_procesamiento, 2)
        }
    
    def _preparar_caracteristicas(self, caracteristicas: Dict) -> np.ndarray:
        valores = []
        
        for nombre_caracteristica in self.caracteristicas_modelo:
            if nombre_caracteristica in caracteristicas:
                valores.append(caracteristicas[nombre_caracteristica])
            else:
                valores.append(0)
        
        return np.array(valores).reshape(1, -1)
    
    def _calcular_puntaje_riesgo(self, probabilidades: np.ndarray) -> int:
        puntajes = [10, 30, 50, 70, 90]
        puntaje = sum(prob * puntaje for prob, puntaje in zip(probabilidades, puntajes))
        return int(puntaje)
    
    def generar_embeddings(self, datos_categoricos: Dict) -> Dict:
        dimension_embedding = 128
        
        embedding_sector = np.random.rand(dimension_embedding)
        embedding_ciudad = np.random.rand(dimension_embedding)
        embedding_educacion = np.random.rand(dimension_embedding)
        
        embedding_concatenado = np.concatenate([
            embedding_sector,
            embedding_ciudad,
            embedding_educacion
        ])
        
        return {
            "embedding_categoricas": embedding_concatenado.tolist(),
            "dimension_embedding": len(embedding_concatenado),
            "componentes": {
                "sector_negocio": embedding_sector.tolist()[:10],
                "ciudad": embedding_ciudad.tolist()[:10],
                "nivel_educacion": embedding_educacion.tolist()[:10]
            }
        }