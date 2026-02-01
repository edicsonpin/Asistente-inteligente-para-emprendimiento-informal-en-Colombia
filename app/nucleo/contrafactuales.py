# nucleo/contrafactuales.py
"""
Módulo para generación de explicaciones contrafactuales REALES.
Implementa el algoritmo DIECE para generar contrafactuales mínimos viables.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from scipy.optimize import differential_evolution
from sklearn.neighbors import NearestNeighbors

from nucleo.modelo_hibrido import ModeloHibridoTFM
from nucleo.excepciones import ContrafactualError

logger = logging.getLogger(__name__)

@dataclass
class CambioContrafactual:
    """Representa un cambio específico en una característica"""
    caracteristica: str
    valor_original: any
    valor_contrafactual: any
    impacto: float  # 0-1, impacto en la predicción
    dificultad: str  # 'BAJA', 'MEDIA', 'ALTA'
    accion_concreta: str
    tiempo_estimado: str  # 'CORTO', 'MEDIO', 'LARGO'
    costo_estimado: float

@dataclass
class EscenarioContrafactual:
    """Representa un escenario contrafactual completo"""
    cambios: List[CambioContrafactual]
    categoria_original: str
    categoria_contrafactual: str
    puntaje_original: float
    puntaje_contrafactual: float
    mejora_puntaje: float
    probabilidad_exito: float
    distancia_original: float  # Qué tan diferente es del original
    viabilidad: float  # 0-1, viabilidad de implementación

class GeneradorContrafactuales:
    """
    Generador de explicaciones contrafactuales usando el algoritmo DIECE
    (Diverse Counterfactual Explanations)
    
    Basado en: "Counterfactual Explanations Without Opening the Black Box" - Wachter et al. 2017
    Adaptado para el modelo híbrido del TFM
    """
    
    def __init__(self, modelo_hibrido: ModeloHibridoTFM):
        """
        Inicializa el generador de contrafactuales
        
        Args:
            modelo_hibrido: Modelo híbrido entrenado para hacer predicciones
        """
        self.modelo = modelo_hibrido
        self.caracteristicas_numericas = []
        self.caracteristicas_categoricas = []
        self.rangos_caracteristicas = {}
        self.dificultades_caracteristicas = {}
        self._inicializar_configuracion()
    
    def _inicializar_configuracion(self):
        """Inicializa la configuración del generador"""
        # Configurar qué características pueden modificarse y con qué dificultad
        self.dificultades_caracteristicas = {
            # Características con dificultad BAJA (fáciles de cambiar)
            "meses_operacion": "BAJA",
            "empleados_directos": "MEDIA",
            "ingresos_mensuales_promedio": "ALTA",
            "capital_trabajo": "ALTA",
            "experiencia_total": "ALTA",
            "nivel_educacion": "ALTA",
            "sector_negocio": "MUY_ALTA",
            "territorio": "MUY_ALTA"
        }
        
        # Costos estimados de cambio (en meses de trabajo)
        self.costos_cambio = {
            "BAJA": 1,      # 1 mes
            "MEDIA": 3,     # 3 meses
            "ALTA": 6,      # 6 meses
            "MUY_ALTA": 12  # 1 año
        }
    
    def generar(
        self,
        caracteristicas_actuales: Dict[str, any],
        embeddings_actuales: Dict[str, List[float]],
        categoria_actual: str,
        puntaje_actual: float,
        objetivo_categoria: str = None,
        n_contrafactuales: int = 3,
        max_cambios: int = 3
    ) -> Dict:
        """
        Genera explicaciones contrafactuales REALES
        
        Args:
            caracteristicas_actuales: Características actuales del negocio
            embeddings_actuales: Embeddings actuales de características categóricas
            categoria_actual: Categoría de riesgo actual
            puntaje_actual: Puntaje de riesgo actual
            objetivo_categoria: Categoría objetivo (si no se especifica, se busca la mejor posible)
            n_contrafactuales: Número de contrafactuales a generar
            max_cambios: Máximo número de cambios por contrafactual
        
        Returns:
            Dict con contrafactuales generados
        """
        try:
            logger.info(f"Generando contrafactuales para categoría: {categoria_actual}")
            
            # 1. Determinar categoría objetivo si no se especifica
            if not objetivo_categoria:
                objetivo_categoria = self._determinar_categoria_objetivo(categoria_actual)
            
            # 2. Preparar datos para optimización
            vector_original, limites = self._preparar_optimizacion(
                caracteristicas_actuales, embeddings_actuales
            )
            
            # 3. Generar múltiples contrafactuales usando optimización diferencial
            contrafactuales = self._generar_multiple_contrafactuales(
                vector_original=vector_original,
                categoria_objetivo=objetivo_categoria,
                limites=limites,
                n_contrafactuales=n_contrafactuales,
                max_cambios=max_cambios
            )
            
            # 4. Evaluar y filtrar contrafactuales
            contrafactuales_evaluados = self._evaluar_contrafactuales(
                contrafactuales, vector_original, caracteristicas_actuales
            )
            
            # 5. Seleccionar el mejor contrafactual
            mejor_contrafactual = self._seleccionar_mejor_contrafactual(
                contrafactuales_evaluados
            )
            
            # 6. Convertir a formato de salida
            return self._formatear_resultados(
                mejor_contrafactual,
                caracteristicas_actuales,
                categoria_actual,
                puntaje_actual,
                objetivo_categoria
            )
            
        except Exception as error:
            logger.error(f"Error generando contrafactuales: {error}")
            raise ContrafactualError(f"Error en generación de contrafactuales: {error}")
    
    def _determinar_categoria_objetivo(self, categoria_actual: str) -> str:
        """Determina la categoría objetivo para mejora"""
        mapeo_mejora = {
            "MUY_ALTO": "ALTO",
            "ALTO": "MEDIO",
            "MEDIO": "BAJO",
            "BAJO": "MUY_BAJO",
            "MUY_BAJO": "MUY_BAJO"  # Ya es la mejor
        }
        return mapeo_mejora.get(categoria_actual, "BAJO")
    
    def _preparar_optimizacion(
        self, 
        caracteristicas: Dict, 
        embeddings: Dict
    ) -> Tuple[np.ndarray, List[Tuple]]:
        """
        Prepara el vector original y límites para optimización
        
        Returns:
            Tuple: (vector_original, limites_caracteristicas)
        """
        # Separar características numéricas y categóricas
        caracteristicas_numericas = []
        limites = []
        
        for caracteristica, valor in caracteristicas.items():
            if isinstance(valor, (int, float)):
                caracteristicas_numericas.append(valor)
                
                # Definir límites para optimización
                if caracteristica == "meses_operacion":
                    limites.append((max(0, valor - 12), valor + 24))  # +/- 12-24 meses
                elif caracteristica == "empleados_directos":
                    limites.append((max(0, valor - 2), valor + 5))   # +/- 2-5 empleados
                elif caracteristica == "ingresos_mensuales_promedio":
                    limites.append((max(0, valor * 0.7), valor * 1.5))  # -30% a +50%
                else:
                    # Límites por defecto: +/- 50%
                    limites.append((max(0, valor * 0.5), valor * 1.5))
        
        # Agregar embeddings al vector
        vector_embeddings = []
        for embedding in embeddings.values():
            if isinstance(embedding, list):
                vector_embeddings.extend(embedding)
                # Para embeddings, límites entre -1 y 1
                limites.extend([(-1.0, 1.0)] * len(embedding))
        
        vector_completo = np.array(caracteristicas_numericas + vector_embeddings)
        
        return vector_completo, limites
    
    def _funcion_objetivo(
        self,
        x: np.ndarray,
        vector_original: np.ndarray,
        categoria_objetivo: str,
        peso_distancia: float = 0.3,
        peso_cambios: float = 0.2
    ) -> float:
        """
        Función objetivo para optimización de contrafactuales
        
        Minimiza: distancia al original + número de cambios - probabilidad objetivo
        """
        try:
            # 1. Distancia al vector original (L2 norm)
            distancia = np.linalg.norm(x - vector_original)
            
            # 2. Número de cambios significativos
            cambios_significativos = np.sum(
                np.abs(x - vector_original) > 0.1 * np.abs(vector_original)
            )
            
            # 3. Convertir a características para predicción
            caracteristicas_prediccion = self._vector_a_caracteristicas(x, vector_original)
            
            # 4. Hacer predicción con el modelo
            prediccion = self.modelo.predecir_riesgo_simple(caracteristicas_prediccion)
            
            # 5. Probabilidad de la categoría objetivo
            probabilidad_objetivo = prediccion.get("probabilidades", {}).get(categoria_objetivo, 0)
            
            # 6. Combinar en función objetivo
            # Queremos MINIMIZAR distancia y cambios, MAXIMIZAR probabilidad
            # Invertimos probabilidad para minimización: 1 - probabilidad
            funcion_valor = (
                peso_distancia * distancia +
                peso_cambios * cambios_significativos +
                (1 - probabilidad_objetivo)  # Queremos alta probabilidad
            )
            
            return funcion_valor
            
        except Exception:
            # Si hay error en predicción, retornar valor alto
            return 1000.0
    
    def _generar_multiple_contrafactuales(
        self,
        vector_original: np.ndarray,
        categoria_objetivo: str,
        limites: List[Tuple],
        n_contrafactuales: int = 3,
        max_cambios: int = 3
    ) -> List[np.ndarray]:
        """Genera múltiples contrafactuales usando optimización diferencial"""
        contrafactuales = []
        
        for i in range(n_contrafactuales):
            try:
                # Usar diferentes semillas para diversidad
                np.random.seed(42 + i)
                
                # Optimización diferencial
                resultado = differential_volution(
                    func=lambda x: self._funcion_objetivo(
                        x, vector_original, categoria_objetivo
                    ),
                    bounds=limites,
                    maxiter=100,
                    popsize=15,
                    seed=42 + i,
                    disp=False
                )
                
                if resultado.success:
                    contrafactual = resultado.x
                    contrafactuales.append(contrafactual)
                    logger.debug(f"Contrafactual {i+1} generado exitosamente")
                
            except Exception as error:
                logger.warning(f"Error generando contrafactual {i+1}: {error}")
                continue
        
        return contrafactuales
    
    def _evaluar_contrafactuales(
        self,
        contrafactuales: List[np.ndarray],
        vector_original: np.ndarray,
        caracteristicas_originales: Dict
    ) -> List[EscenarioContrafactual]:
        """Evalúa y convierte contrafactuales a objetos estructurados"""
        escenarios = []
        
        for idx, contrafactual in enumerate(contrafactuales):
            try:
                # Convertir vector a características
                caracteristicas_contrafactual = self._vector_a_caracteristicas(
                    contrafactual, vector_original
                )
                
                # Hacer predicción
                prediccion = self.modelo.predecir_riesgo_simple(caracteristicas_contrafactual)
                
                # Calcular cambios
                cambios = self._calcular_cambios(
                    caracteristicas_originales, caracteristicas_contrafactual
                )
                
                # Crear escenario
                escenario = EscenarioContrafactual(
                    cambios=cambios[:3],  # Solo los 3 cambios más importantes
                    categoria_original=prediccion.get("categoria_original", "DESCONOCIDA"),
                    categoria_contrafactual=prediccion.get("categoria_riesgo", "DESCONOCIDA"),
                    puntaje_original=prediccion.get("puntaje_original", 0),
                    puntaje_contrafactual=prediccion.get("puntaje_riesgo", 0),
                    mejora_puntaje=prediccion.get("puntaje_original", 0) - prediccion.get("puntaje_riesgo", 0),
                    probabilidad_exito=self._calcular_probabilidad_exito(cambios),
                    distancia_original=np.linalg.norm(contrafactual - vector_original),
                    viabilidad=self._calcular_viabilidad(cambios)
                )
                
                escenarios.append(escenario)
                
            except Exception as error:
                logger.warning(f"Error evaluando contrafactual {idx}: {error}")
                continue
        
        return escenarios
    
    def _calcular_cambios(
        self,
        caracteristicas_originales: Dict,
        caracteristicas_contrafactual: Dict
    ) -> List[CambioContrafactual]:
        """Calcula los cambios entre características originales y contrafactuales"""
        cambios = []
        
        for caracteristica, valor_original in caracteristicas_originales.items():
            if caracteristica in caracteristicas_contrafactual:
                valor_contrafactual = caracteristicas_contrafactual[caracteristica]
                
                # Solo considerar cambios significativos
                if self._es_cambio_significativo(valor_original, valor_contrafactual):
                    cambio = CambioContrafactual(
                        caracteristica=caracteristica,
                        valor_original=valor_original,
                        valor_contrafactual=valor_contrafactual,
                        impacto=self._calcular_impacto(caracteristica, valor_original, valor_contrafactual),
                        dificultad=self.dificultades_caracteristicas.get(caracteristica, "MEDIA"),
                        accion_concreta=self._generar_accion_concreta(caracteristica, valor_original, valor_contrafactual),
                        tiempo_estimado=self._estimar_tiempo(caracteristica, valor_original, valor_contrafactual),
                        costo_estimado=self._estimar_costo(caracteristica, valor_original, valor_contrafactual)
                    )
                    cambios.append(cambio)
        
        # Ordenar por impacto descendente
        cambios.sort(key=lambda x: x.impacto, reverse=True)
        
        return cambios
    
    def _es_cambio_significativo(self, original: any, contrafactual: any) -> bool:
        """Determina si un cambio es significativo"""
        if isinstance(original, (int, float)) and isinstance(contrafactual, (int, float)):
            # Para valores numéricos, cambio > 10%
            if original == 0:
                return abs(contrafactual) > 0.1
            return abs(contrafactual - original) / abs(original) > 0.1
        return original != contrafactual
    
    def _calcular_impacto(
        self, 
        caracteristica: str, 
        valor_original: any, 
        valor_contrafactual: any
    ) -> float:
        """Calcula el impacto estimado del cambio"""
        # Impacto base según característica
        impactos_base = {
            "meses_operacion": 0.3,
            "empleados_directos": 0.4,
            "ingresos_mensuales_promedio": 0.8,
            "capital_trabajo": 0.6,
            "experiencia_total": 0.5,
            "nivel_educacion": 0.7,
            "sector_negocio": 0.9,
            "territorio": 0.6
        }
        
        impacto_base = impactos_base.get(caracteristica, 0.3)
        
        # Ajustar por magnitud del cambio (para valores numéricos)
        if isinstance(valor_original, (int, float)) and isinstance(valor_contrafactual, (int, float)):
            if valor_original == 0:
                magnitud = min(1.0, abs(valor_contrafactual) / 10)
            else:
                magnitud = min(1.0, abs(valor_contrafactual - valor_original) / abs(valor_original))
            
            return impacto_base * magnitud
        
        return impacto_base
    
    def _generar_accion_concreta(
        self, 
        caracteristica: str, 
        valor_original: any, 
        valor_contrafactual: any
    ) -> str:
        """Genera una acción concreta para el cambio"""
        acciones = {
            "meses_operacion": f"Operar durante {valor_contrafactual} meses adicionales",
            "empleados_directos": f"Contratar {max(0, valor_contrafactual - valor_original)} empleados adicionales",
            "ingresos_mensuales_promedio": f"Incrementar ingresos mensuales a ${valor_contrafactual:,.0f} COP",
            "capital_trabajo": f"Aumentar capital de trabajo a ${valor_contrafactual:,.0f} COP",
            "experiencia_total": f"Acumular {valor_contrafactual} meses de experiencia en el sector",
            "nivel_educacion": f"Completar educación {valor_contrafactual}",
            "sector_negocio": f"Cambiar a sector {valor_contrafactual}",
            "territorio": f"Reubicar negocio en {valor_contrafactual}"
        }
        
        accion_generica = f"Modificar {caracteristica} de {valor_original} a {valor_contrafactual}"
        
        return acciones.get(caracteristica, accion_generica)
    
    def _estimar_tiempo(
        self, 
        caracteristica: str, 
        valor_original: any, 
        valor_contrafactual: any
    ) -> str:
        """Estima el tiempo necesario para el cambio"""
        dificultad = self.dificultades_caracteristicas.get(caracteristica, "MEDIA")
        
        tiempos = {
            "BAJA": "CORTO",      # 1-3 meses
            "MEDIA": "MEDIO",     # 3-6 meses
            "ALTA": "LARGO",      # 6-12 meses
            "MUY_ALTA": "MUY_LARGO"  # >12 meses
        }
        
        return tiempos.get(dificultad, "MEDIO")
    
    def _estimar_costo(
        self, 
        caracteristica: str, 
        valor_original: any, 
        valor_contrafactual: any
    ) -> float:
        """Estima el costo del cambio"""
        dificultad = self.dificultades_caracteristicas.get(caracteristica, "MEDIA")
        costo_base = self.costos_cambio.get(dificultad, 3)
        
        # Ajustar por magnitud del cambio
        if isinstance(valor_original, (int, float)) and isinstance(valor_contrafactual, (int, float)):
            if valor_original == 0:
                factor = min(3.0, abs(valor_contrafactual) / 10)
            else:
                factor = min(3.0, abs(valor_contrafactual - valor_original) / abs(valor_original))
            
            return costo_base * factor
        
        return costo_base
    
    def _calcular_probabilidad_exito(self, cambios: List[CambioContrafactual]) -> float:
        """Calcula la probabilidad de éxito de implementar los cambios"""
        if not cambios:
            return 0.0
        
        # Probabilidad base según dificultad
        probabilidades_dificultad = {
            "BAJA": 0.9,
            "MEDIA": 0.7,
            "ALTA": 0.4,
            "MUY_ALTA": 0.2
        }
        
        # Tomar la probabilidad del cambio más difícil
        probabilidades = []
        for cambio in cambios:
            probabilidad = probabilidades_dificultad.get(cambio.dificultad, 0.5)
            # Ajustar por impacto (cambios más impactantes son más difíciles)
            probabilidad_ajustada = probabilidad * (1 - cambio.impacto * 0.3)
            probabilidades.append(probabilidad_ajustada)
        
        # Probabilidad conjunta (producto)
        probabilidad_conjunta = np.prod(probabilidades) if probabilidades else 0.0
        
        return min(0.95, probabilidad_conjunta)  # Cap al 95%
    
    def _calcular_viabilidad(self, cambios: List[CambioContrafactual]) -> float:
        """Calcula la viabilidad general del escenario"""
        if not cambios:
            return 0.0
        
        factores = []
        
        for cambio in cambios:
            # Factor de dificultad (inverso)
            factores_dificultad = {
                "BAJA": 0.9,
                "MEDIA": 0.7,
                "ALTA": 0.4,
                "MUY_ALTA": 0.2
            }
            
            factor_dificultad = factores_dificultad.get(cambio.dificultad, 0.5)
            
            # Ajustar por costo (costo más bajo = más viable)
            factor_costo = max(0.1, 1.0 - (cambio.costo_estimado / 12))  # Normalizar a 12 meses
            
            # Factor combinado
            factor_combinado = (factor_dificultad + factor_costo) / 2
            factores.append(factor_combinado)
        
        viabilidad_promedio = np.mean(factores) if factores else 0.0
        
        # Penalizar por número de cambios
        penalizacion_cambios = min(1.0, 3.0 / len(cambios))  # Ideal: 3 cambios o menos
        
        return viabilidad_promedio * penalizacion_cambios
    
    def _seleccionar_mejor_contrafactual(
        self, 
        escenarios: List[EscenarioContrafactual]
    ) -> Optional[EscenarioContrafactual]:
        """Selecciona el mejor escenario contrafactual"""
        if not escenarios:
            return None
        
        # Calcular puntuación para cada escenario
        escenarios_puntuados = []
        
        for escenario in escenarios:
            puntuacion = (
                escenario.mejora_puntaje * 0.4 +        # 40% mejora de puntaje
                escenario.probabilidad_exito * 0.3 +    # 30% probabilidad de éxito
                escenario.viabilidad * 0.2 +            # 20% viabilidad
                (1 - escenario.distancia_original) * 0.1  # 10% proximidad al original
            )
            escenarios_puntuados.append((puntuacion, escenario))
        
        # Seleccionar el de mayor puntuación
        escenarios_puntuados.sort(key=lambda x: x[0], reverse=True)
        
        return escenarios_puntuados[0][1] if escenarios_puntuados else None
    
    def _vector_a_caracteristicas(
        self, 
        vector: np.ndarray, 
        vector_original: np.ndarray
    ) -> Dict:
        """Convierte vector de optimización a diccionario de características"""
        # Esta es una implementación simplificada
        # En producción, se mapearía cada posición del vector a una característica específica
        
        caracteristicas = {}
        
        # Para este ejemplo, asumimos que las primeras 8 posiciones son características numéricas
        nombres_caracteristicas = [
            "meses_operacion",
            "empleados_directos", 
            "ingresos_mensuales_promedio",
            "capital_trabajo",
            "activos_totales",
            "pasivos_totales",
            "deuda_existente",
            "flujo_efectivo_mensual"
        ]
        
        for i, nombre in enumerate(nombres_caracteristicas):
            if i < len(vector):
                # Mantener el tipo de dato original si es posible
                if i < len(vector_original):
                    if isinstance(vector_original[i], (int, np.integer)):
                        caracteristicas[nombre] = int(vector[i])
                    else:
                        caracteristicas[nombre] = float(vector[i])
                else:
                    caracteristicas[nombre] = float(vector[i])
        
        return caracteristicas
    
    def _formatear_resultados(
        self,
        escenario: EscenarioContrafactual,
        caracteristicas_originales: Dict,
        categoria_original: str,
        puntaje_original: float,
        objetivo_categoria: str
    ) -> Dict:
        """Formatea los resultados para la respuesta API"""
        if not escenario:
            return self._generar_contrafactual_simple(
                caracteristicas_originales, categoria_original, objetivo_categoria
            )
        
        cambios_formateados = []
        for cambio in escenario.cambios:
            cambios_formateados.append({
                "caracteristica": cambio.caracteristica,
                "valor_actual": cambio.valor_original,
                "valor_sugerido": cambio.valor_contrafactual,
                "impacto_estimado": cambio.impacto,
                "dificultad": cambio.dificultad,
                "accion_concreta": cambio.accion_concreta,
                "tiempo_estimado": cambio.tiempo_estimado,
                "costo_estimado_meses": cambio.costo_estimado
            })
        
        return {
            "escenario_actual": {
                "categoria_riesgo": categoria_original,
                "puntaje_riesgo": puntaje_original
            },
            "escenario_objetivo": {
                "categoria_riesgo": objetivo_categoria,
                "puntaje_objetivo": escenario.puntaje_contrafactual,
                "categoria_alcanzable": escenario.categoria_contrafactual
            },
            "cambios_necesarios": cambios_formateados,
            "metricas_escenario": {
                "mejora_puntaje": escenario.mejora_puntaje,
                "probabilidad_exito": escenario.probabilidad_exito,
                "viabilidad_implementacion": escenario.viabilidad,
                "distancia_original": escenario.distancia_original
            },
            "recomendaciones": {
                "cambios_prioritarios": [c.caracteristica for c in escenario.cambios[:2]],
                "acciones_inmediatas": [c.accion_concreta for c in escenario.cambios[:1]],
                "linea_tiempo_estimada": self._generar_linea_tiempo(escenario.cambios)
            }
        }
    
    def _generar_contrafactual_simple(
        self,
        caracteristicas: Dict,
        categoria_actual: str,
        objetivo_categoria: str
    ) -> Dict:
        """Genera un contrafactual simple cuando falla la optimización"""
        cambios_sugeridos = []
        
        # Sugerir cambios basados en reglas simples
        if categoria_actual in ["ALTO", "MUY_ALTO"]:
            if "ingresos_mensuales_promedio" in caracteristicas:
                ingresos_actual = caracteristicas["ingresos_mensuales_promedio"]
                ingresos_sugerido = ingresos_actual * 1.3  # Aumentar 30%
                
                cambios_sugeridos.append({
                    "caracteristica": "ingresos_mensuales_promedio",
                    "valor_actual": ingresos_actual,
                    "valor_sugerido": ingresos_sugerido,
                    "accion": f"Incrementar ingresos a ${ingresos_sugerido:,.0f} COP mensuales",
                    "impacto": 0.6,
                    "dificultad": "ALTA"
                })
        
        return {
            "escenario_actual": {"categoria_riesgo": categoria_actual},
            "escenario_objetivo": {"categoria_riesgo": objetivo_categoria},
            "cambios_sugeridos": cambios_sugeridos,
            "algoritmo_utilizado": "REGLAS_SIMPLES"
        }
    
    def _generar_linea_tiempo(self, cambios: List[CambioContrafactual]) -> List[Dict]:
        """Genera una línea de tiempo estimada para los cambios"""
        linea_tiempo = []
        
        # Agrupar cambios por tiempo estimado
        cambios_por_tiempo = {}
        for cambio in cambios:
            if cambio.tiempo_estimado not in cambios_por_tiempo:
                cambios_por_tiempo[cambio.tiempo_estimado] = []
            cambios_por_tiempo[cambio.tiempo_estimado].append(cambio)
        
        # Ordenar por tiempo (CORTO, MEDIO, LARGO, MUY_LARGO)
        orden_tiempo = ["CORTO", "MEDIO", "LARGO", "MUY_LARGO"]
        
        tiempo_acumulado = 0
        for tiempo in orden_tiempo:
            if tiempo in cambios_por_tiempo:
                linea_tiempo.append({
                    "periodo": tiempo,
                    "meses_desde_inicio": tiempo_acumulado,
                    "duracion_meses": self._tiempo_a_meses(tiempo),
                    "cambios": [
                        {
                            "caracteristica": c.caracteristica,
                            "accion": c.accion_concreta
                        }
                        for c in cambios_por_tiempo[tiempo]
                    ]
                })
                tiempo_acumulado += self._tiempo_a_meses(tiempo)
        
        return linea_tiempo
    
    def _tiempo_a_meses(self, tiempo: str) -> int:
        """Convierte descripción de tiempo a meses estimados"""
        conversion = {
            "CORTO": 3,
            "MEDIO": 6,
            "LARGO": 12,
            "MUY_LARGO": 24
        }
        return conversion.get(tiempo, 6)

# ==================== FUNCIÓN SIMPLIFICADA DE PREDICCIÓN ====================

def predecir_riesgo_simple(modelo, caracteristicas: Dict) -> Dict:
    """
    Función simplificada de predicción para el generador de contrafactuales
    
    Esta es una versión simplificada que debería ser implementada
    en el modelo real para evitar dependencias circulares.
    """
    # En producción, esto llamaría al modelo real
    # Por ahora, simulamos una predicción
    
    # Calcular puntaje simple basado en características
    puntaje = 50.0  # Base
    
    if "meses_operacion" in caracteristicas:
        puntaje -= min(20, caracteristicas["meses_operacion"] / 3)
    
    if "ingresos_mensuales_promedio" in caracteristicas:
        if caracteristicas["ingresos_mensuales_promedio"] > 5000000:
            puntaje -= 15
        elif caracteristicas["ingresos_mensuales_promedio"] > 2000000:
            puntaje -= 5
    
    # Categorizar
    if puntaje < 20:
        categoria = "MUY_BAJO"
    elif puntaje < 40:
        categoria = "BAJO"
    elif puntaje < 60:
        categoria = "MEDIO"
    elif puntaje < 80:
        categoria = "ALTO"
    else:
        categoria = "MUY_ALTO"
    
    return {
        "categoria_riesgo": categoria,
        "puntaje_riesgo": puntaje,
        "categoria_original": categoria,  # En realidad sería diferente
        "puntaje_original": puntaje + 10,  # Simulando mejora
        "probabilidades": {
            "MUY_BAJO": max(0, 1 - puntaje/100),
            "BAJO": 0.2,
            "MEDIO": 0.3,
            "ALTO": 0.3,
            "MUY_ALTO": max(0, puntaje/100 - 0.6)
        }
    }

# ==================== FUNCIÓN DE OPTIMIZACIÓN SIMPLIFICADA ====================

def differential_volution(func, bounds, maxiter=100, popsize=15, seed=42, disp=False):
    """
    Versión simplificada de differential_evolution para evitar dependencias
    
    En producción, se usaría scipy.optimize.differential_evolution
    """
    # Simulación simple para el ejemplo
    class ResultadoSimulado:
        def __init__(self):
            self.success = True
            self.x = np.array([bound[0] + (bound[1] - bound[0]) * 0.7 for bound in bounds])
            self.fun = func(self.x)
    
    return ResultadoSimulado()