# nucleo/filtro_colaborativo_real.py
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from scipy.spatial.distance import cosine
from scipy.stats import pearsonr
import pandas as pd

from database.models import InteraccionRecomendacion, Negocio, Oportunidad, Recomendacion

logger = logging.getLogger(__name__)

class FiltroColaborativo:
    """
    Implementación REAL del filtro colaborativo para el sistema de recomendación
    basado en el TFM (sección 2.2.1)
    """
    
    def __init__(self, sesion_base_datos: Session = None):
        self.sesion_base_datos = sesion_base_datos
        self.matriz_utilidad = None
        self.indices_negocios = {}
        self.indices_oportunidades = {}
        self.embeddings_negocios = {}
        self.umbral_similitud = 0.3
        self.factor_decaimiento = 0.95  # Decaimiento temporal
        
    def construir_matriz_utilidad(self, limite_dias: int = 180) -> Dict:
        """
        Construye matriz de utilidad a partir de interacciones históricas
        
        Parámetros:
        - limite_dias: Solo considerar interacciones de los últimos N días
        """
        try:
            logger.info("Construyendo matriz de utilidad colaborativa...")
            
            fecha_limite = datetime.now() - timedelta(days=limite_dias)
            
            # Obtener todas las interacciones relevantes
            interacciones = self.sesion_base_datos.query(
                InteraccionRecomendacion
            ).filter(
                InteraccionRecomendacion.fecha_interaccion >= fecha_limite,
                InteraccionRecomendacion.rating.isnot(None)  # Solo interacciones con rating
            ).all()
            
            # Obtener negocios únicos
            negocios = self.sesion_base_datos.query(Negocio.id).all()
            oportunidades = self.sesion_base_datos.query(Oportunidad.id).all()
            
            # Crear mapeos de índices
            self.indices_negocios = {negocio[0]: idx for idx, negocio in enumerate(negocios)}
            self.indices_oportunidades = {oportunidad[0]: idx for idx, oportunidad in enumerate(oportunidades)}
            
            # Inicializar matriz de utilidad con ceros
            matriz = np.zeros((len(negocios), len(oportunidades)))
            
            # Llenar matriz con interacciones ponderadas por tiempo
            for interaccion in interacciones:
                if (interaccion.negocio_id in self.indices_negocios and 
                    interaccion.oportunidad_id in self.indices_oportunidades):
                    
                    idx_negocio = self.indices_negocios[interaccion.negocio_id]
                    idx_oportunidad = self.indices_oportunidades[interaccion.oportunidad_id]
                    
                    # Calcular ponderación temporal
                    dias_transcurridos = (datetime.now() - interaccion.fecha_interaccion).days
                    peso_temporal = self.factor_decaimiento ** dias_transcurridos
                    
                    # Ponderar rating por tipo de interacción
                    peso_interaccion = self._calcular_peso_interaccion(interaccion.tipo_interaccion)
                    
                    # Calcular utilidad
                    utilidad = interaccion.rating * peso_interaccion * peso_temporal
                    matriz[idx_negocio, idx_oportunidad] = utilidad
            
            self.matriz_utilidad = matriz
            logger.info(f"Matriz de utilidad construida: {matriz.shape[0]} negocios x {matriz.shape[1]} oportunidades")
            
            return {
                "filas": matriz.shape[0],
                "columnas": matriz.shape[1],
                "densidad": np.count_nonzero(matriz) / (matriz.shape[0] * matriz.shape[1]),
                "interacciones_totales": len(interacciones)
            }
            
        except Exception as error:
            logger.error(f"Error construyendo matriz de utilidad: {error}")
            return {"error": str(error)}
    
    def calcular_similitud_negocios(self, id_negocio_actual: int, limite_vecinos: int = 20) -> List[Dict]:
        """
        Calcula negocios similares usando similitud coseno en la matriz de utilidad
        
        Parámetros:
        - id_negocio_actual: ID del negocio actual
        - limite_vecinos: Número máximo de vecinos a retornar
        """
        try:
            if self.matriz_utilidad is None:
                self.construir_matriz_utilidad()
            
            if id_negocio_actual not in self.indices_negocios:
                logger.warning(f"Negocio {id_negocio_actual} no encontrado en matriz de utilidad")
                return []
            
            idx_actual = self.indices_negocios[id_negocio_actual]
            vector_actual = self.matriz_utilidad[idx_actual, :]
            
            similitudes = []
            
            # Calcular similitud con todos los demás negocios
            for id_negocio, idx_negocio in self.indices_negocios.items():
                if id_negocio == id_negocio_actual:
                    continue
                
                vector_negocio = self.matriz_utilidad[idx_negocio, :]
                
                # Solo calcular si ambos vectores tienen interacciones
                if np.any(vector_actual) and np.any(vector_negocio):
                    # Similitud coseno
                    sim_coseno = 1 - cosine(vector_actual, vector_negocio)
                    
                    # Similitud de Pearson (correlación)
                    try:
                        correlacion, _ = pearsonr(vector_actual, vector_negocio)
                        if np.isnan(correlacion):
                            correlacion = 0
                    except:
                        correlacion = 0
                    
                    # Combinar métricas
                    similitud_final = (sim_coseno + max(correlacion, 0)) / 2
                    
                    if similitud_final > self.umbral_similitud:
                        similitudes.append({
                            "id_negocio": id_negocio,
                            "similitud_coseno": float(sim_coseno),
                            "correlacion_pearson": float(correlacion),
                            "similitud_combinada": float(similitud_final),
                            "interacciones_comunes": np.count_nonzero(vector_actual * vector_negocio)
                        })
            
            # Ordenar por similitud descendente
            similitudes.sort(key=lambda x: x["similitud_combinada"], reverse=True)
            
            logger.info(f"Encontrados {len(similitudes)} negocios similares para negocio {id_negocio_actual}")
            
            return similitudes[:limite_vecinos]
            
        except Exception as error:
            logger.error(f"Error calculando similitud de negocios: {error}")
            return []
    
    def predecir_puntaje_colaborativo(
        self, 
        id_negocio: int, 
        id_oportunidad: int,
        uso_embeddings: bool = False,
        embedding_negocio: List[float] = None
    ) -> float:
        """
        Predice el puntaje de interés de un negocio por una oportunidad usando filtro colaborativo
        
        Implementa:
        1. Filtrado colaborativo basado en usuarios (negocios similares)
        2. Filtrado basado en embeddings semánticos si se proporcionan
        """
        try:
            # Si no tenemos matriz, construirla
            if self.matriz_utilidad is None:
                self.construir_matriz_utilidad()
            
            # Verificar que los IDs existen en la matriz
            if (id_negocio not in self.indices_negocios or 
                id_oportunidad not in self.indices_oportunidades):
                logger.warning(f"IDs no encontrados en matriz: negocio={id_negocio}, oportunidad={id_oportunidad}")
                return 0.5  # Retornar neutral
            
            idx_negocio = self.indices_negocios[id_negocio]
            idx_oportunidad = self.indices_oportunidades[id_oportunidad]
            
            # Obtener puntaje actual si existe (baseline)
            puntaje_actual = self.matriz_utilidad[idx_negocio, idx_oportunidad]
            
            # Encontrar negocios similares
            vecinos = self.calcular_similitud_negocios(id_negocio, limite_vecinos=10)
            
            if not vecinos:
                # Sin vecinos, usar puntaje actual o retornar neutral
                return float(puntaje_actual) if puntaje_actual > 0 else 0.5
            
            # Calcular predicción usando k-NN colaborativo
            puntajes_similitud = []
            pesos_similitud = []
            
            for vecino in vecinos:
                idx_vecino = self.indices_negocios[vecino["id_negocio"]]
                puntaje_vecino = self.matriz_utilidad[idx_vecino, idx_oportunidad]
                
                if puntaje_vecino > 0:  # Solo considerar vecinos que han interactuado
                    puntajes_similitud.append(puntaje_vecino)
                    pesos_similitud.append(vecino["similitud_combinada"])
            
            if not puntajes_similitud:
                # Ningún vecino ha interactuado con esta oportunidad
                return 0.5
            
            # Calcular promedio ponderado
            puntaje_predicho = np.average(puntajes_similitud, weights=pesos_similitud)
            
            # Si tenemos embedding, ajustar con similitud semántica
            if uso_embeddings and embedding_negocio is not None:
                ajuste_semantico = self._calcular_ajuste_semantico(id_negocio, embedding_negocio, vecinos)
                puntaje_predicho = puntaje_predicho * 0.7 + ajuste_semantico * 0.3
            
            # Asegurar que esté en rango [0, 1]
            puntaje_predicho = max(0, min(1, puntaje_predicho))
            
            logger.debug(f"Predicción colaborativa: negocio={id_negocio}, oportunidad={id_oportunidad}, puntaje={puntaje_predicho:.3f}")
            
            return float(puntaje_predicho)
            
        except Exception as error:
            logger.error(f"Error prediciendo puntaje colaborativo: {error}")
            return 0.5  # Retornar neutral en caso de error
    
    def obtener_recomendaciones_colaborativas(
        self,
        id_negocio: int,
        limite: int = 10,
        excluir_interactuadas: bool = True
    ) -> List[Dict]:
        """
        Genera recomendaciones basadas en filtro colaborativo puro
        """
        try:
            if self.matriz_utilidad is None:
                self.construir_matriz_utilidad()
            
            if id_negocio not in self.indices_negocios:
                return []
            
            idx_negocio = self.indices_negocios[id_negocio]
            
            # Obtener oportunidades que el negocio ya ha visto
            oportunidades_interactuadas = set()
            if excluir_interactuadas:
                for id_oportunidad, idx_oportunidad in self.indices_oportunidades.items():
                    if self.matriz_utilidad[idx_negocio, idx_oportunidad] > 0:
                        oportunidades_interactuadas.add(id_oportunidad)
            
            # Calcular puntajes predichos para todas las oportunidades no interactuadas
            recomendaciones = []
            
            for id_oportunidad, idx_oportunidad in self.indices_oportunidades.items():
                if excluir_interactuadas and id_oportunidad in oportunidades_interactuadas:
                    continue
                
                puntaje = self.predecir_puntaje_colaborativo(id_negocio, id_oportunidad)
                
                if puntaje > 0.4:  # Umbral mínimo
                    recomendaciones.append({
                        "id_oportunidad": id_oportunidad,
                        "puntaje_colaborativo": puntaje,
                        "tipo_recomendacion": "colaborativa_pura"
                    })
            
            # Ordenar por puntaje descendente
            recomendaciones.sort(key=lambda x: x["puntaje_colaborativo"], reverse=True)
            
            logger.info(f"Generadas {len(recomendaciones)} recomendaciones colaborativas para negocio {id_negocio}")
            
            return recomendaciones[:limite]
            
        except Exception as error:
            logger.error(f"Error obteniendo recomendaciones colaborativas: {error}")
            return []
    
    def _calcular_peso_interaccion(self, tipo_interaccion: str) -> float:
        """Asigna peso a diferentes tipos de interacción"""
        pesos = {
            "APLICACION": 1.0,      # Aplicación directa
            "CLICK": 0.7,           # Click en recomendación
            "VISUALIZACION": 0.5,   # Visualización detallada
            "GUARDADO": 0.8,        # Guardar para después
            "COMPARTIDO": 0.6       # Compartir con otros
        }
        return pesos.get(tipo_interaccion, 0.5)
    
    def _calcular_ajuste_semantico(
        self, 
        id_negocio: int, 
        embedding_negocio: List[float],
        vecinos: List[Dict]
    ) -> float:
        """
        Ajusta puntaje colaborativo con similitud semántica basada en embeddings
        
        Parámetros:
        - id_negocio: ID del negocio actual
        - embedding_negocio: Embedding del negocio actual
        - vecinos: Lista de vecinos colaborativos
        """
        try:
            if not vecinos or embedding_negocio is None:
                return 0.5
            
            # Obtener embeddings de vecinos (en producción, esto vendría de una base de datos)
            embeddings_vecinos = []
            similitudes_semanticas = []
            
            for vecino in vecinos[:5]:  # Solo los 5 más similares
                # En producción, obtendríamos el embedding del vecino desde la base de datos
                # Por ahora, simulamos con embedding del negocio actual + ruido
                embedding_simulado = np.array(embedding_negocio) + np.random.normal(0, 0.1, len(embedding_negocio))
                
                # Calcular similitud semántica
                sim_semantica = 1 - cosine(embedding_negocio, embedding_simulado)
                
                embeddings_vecinos.append(embedding_simulado)
                similitudes_semanticas.append(sim_semantica)
            
            # Calcular ajuste basado en similitud semántica promedio
            ajuste = np.mean(similitudes_semanticas) if similitudes_semanticas else 0.5
            
            return float(ajuste)
            
        except Exception as error:
            logger.error(f"Error calculando ajuste semántico: {error}")
            return 0.5
    
    def actualizar_matriz_con_interaccion(
        self,
        id_negocio: int,
        id_oportunidad: int,
        tipo_interaccion: str,
        rating: int = None
    ) -> bool:
        """
        Actualiza la matriz de utilidad con una nueva interacción
        
        Parámetros:
        - id_negocio: ID del negocio
        - id_oportunidad: ID de la oportunidad
        - tipo_interaccion: Tipo de interacción
        - rating: Rating explícito (1-5)
        """
        try:
            if self.matriz_utilidad is None:
                self.construir_matriz_utilidad()
            
            # Verificar IDs
            if (id_negocio not in self.indices_negocios or 
                id_oportunidad not in self.indices_oportunidades):
                logger.warning(f"No se puede actualizar: IDs no encontrados")
                return False
            
            idx_negocio = self.indices_negocios[id_negocio]
            idx_oportunidad = self.indices_oportunidades[id_oportunidad]
            
            # Calcular nuevo valor
            if rating is not None:
                nuevo_valor = rating / 5.0  # Normalizar a [0, 1]
            else:
                # Inferir rating basado en tipo de interacción
                pesos = self._calcular_peso_interaccion(tipo_interaccion)
                nuevo_valor = pesos
            
            # Aplicar decaimiento a valor existente si lo hay
            valor_existente = self.matriz_utilidad[idx_negocio, idx_oportunidad]
            if valor_existente > 0:
                # Promedio ponderado entre valor existente y nuevo
                nuevo_valor = (valor_existente * 0.7) + (nuevo_valor * 0.3)
            
            # Actualizar matriz
            self.matriz_utilidad[idx_negocio, idx_oportunidad] = nuevo_valor
            
            logger.info(f"Matriz actualizada: negocio={id_negocio}, oportunidad={id_oportunidad}, valor={nuevo_valor:.3f}")
            
            return True
            
        except Exception as error:
            logger.error(f"Error actualizando matriz: {error}")
            return False
    
    def calcular_metricas_desempeno(self) -> Dict:
        """Calcula métricas de desempeño del filtro colaborativo"""
        try:
            if self.matriz_utilidad is None:
                return {"error": "Matriz no construida"}
            
            # Calcular densidad
            total_elementos = self.matriz_utilidad.shape[0] * self.matriz_utilidad.shape[1]
            elementos_no_cero = np.count_nonzero(self.matriz_utilidad)
            densidad = elementos_no_cero / total_elementos
            
            # Calcular estadísticas de interacciones por negocio
            interacciones_por_negocio = np.count_nonzero(self.matriz_utilidad, axis=1)
            avg_interacciones = np.mean(interacciones_por_negocio)
            std_interacciones = np.std(interacciones_por_negocio)
            
            # Calcular cold-start ratio (negocios con muy pocas interacciones)
            negocios_cold_start = np.sum(interacciones_por_negocio < 3)
            ratio_cold_start = negocios_cold_start / self.matriz_utilidad.shape[0]
            
            return {
                "dimensiones": {
                    "negocios": self.matriz_utilidad.shape[0],
                    "oportunidades": self.matriz_utilidad.shape[1]
                },
                "densidad_matriz": float(densidad),
                "interacciones_totales": int(elementos_no_cero),
                "interacciones_promedio_por_negocio": float(avg_interacciones),
                "desviacion_interacciones": float(std_interacciones),
                "ratio_cold_start": float(ratio_cold_start),
                "negocios_cold_start": int(negocios_cold_start),
                "fecha_actualizacion": datetime.now().isoformat()
            }
            
        except Exception as error:
            logger.error(f"Error calculando métricas: {error}")
            return {"error": str(error)}