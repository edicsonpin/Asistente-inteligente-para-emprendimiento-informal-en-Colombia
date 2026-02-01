# nucleo/contrafactuales.py - VERSIÓN CORREGIDA


import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from scipy.optimize import differential_evolution  # ✅ CORRECCIÓN 1: Import correcto
from scipy.spatial.distance import cosine
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
    factible: bool  # ✅ NUEVO: Indica si el cambio es factible

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
    distancia_original: float
    viabilidad: float
    factible: bool  # ✅ NUEVO: Viabilidad general del escenario

class GeneradorContrafactuales:
    """
    Generador de explicaciones contrafactuales usando el algoritmo DiCE
    (Diverse Counterfactual Explanations)
    """
    
    def __init__(self, modelo_hibrido: ModeloHibridoTFM):
        self.modelo = modelo_hibrido
        self.caracteristicas_numericas = []
        self.caracteristicas_categoricas = []
        self.rangos_caracteristicas = {}
        self.dificultades_caracteristicas = {}
        self.restricciones_factibilidad = {}  # ✅ NUEVO
        self.mapeo_indices_caracteristicas = []  # ✅ NUEVO
        self.tipos_caracteristicas = {}  # ✅ NUEVO
        self._inicializar_configuracion()
    
    def _inicializar_configuracion(self):
        """Inicializa la configuración del generador"""
        # Configurar dificultades
        self.dificultades_caracteristicas = {
            "meses_operacion": "BAJA",
            "empleados_directos": "MEDIA",
            "empleados_indirectos": "MEDIA",
            "ingresos_mensuales_promedio": "ALTA",
            "capital_trabajo": "ALTA",
            "activos_totales": "ALTA",
            "pasivos_totales": "ALTA",
            "deuda_existente": "ALTA",
            "flujo_efectivo_mensual": "ALTA",
            "experiencia_total": "ALTA",
            "nivel_educacion": "MUY_ALTA",
            "sector_negocio": "MUY_ALTA",
            "territorio": "MUY_ALTA"
        }
        
        # ✅ NUEVO: Restricciones de factibilidad
        self.restricciones_factibilidad = {
            "meses_operacion": {"min_cambio": 0, "solo_incremento": True},
            "experiencia_total": {"min_cambio": 0, "solo_incremento": True},
            "empleados_directos": {"min_valor": 0, "max_cambio_relativo": 5.0},
            "ingresos_mensuales_promedio": {"min_valor": 0, "max_cambio_relativo": 2.0},
            "capital_trabajo": {"min_valor": 0, "max_cambio_relativo": 3.0},
            "activos_totales": {"min_valor": 0, "max_cambio_relativo": 2.0},
            "deuda_existente": {"min_valor": 0, "max_cambio_relativo": 1.5},
        }
        
        # Costos estimados de cambio
        self.costos_cambio = {
            "BAJA": 1,
            "MEDIA": 3,
            "ALTA": 6,
            "MUY_ALTA": 12
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
        """Genera explicaciones contrafactuales REALES"""
        try:
            logger.info(f"🔄 Generando contrafactuales para categoría: {categoria_actual}")
            
            # 1. Determinar categoría objetivo
            if not objetivo_categoria:
                objetivo_categoria = self._determinar_categoria_objetivo(categoria_actual)
            
            # 2. Preparar datos para optimización
            vector_original, limites, mapeo = self._preparar_optimizacion(
                caracteristicas_actuales, embeddings_actuales
            )
            
            # Guardar mapeo para conversión posterior
            self.mapeo_indices_caracteristicas = mapeo["nombres"]
            self.tipos_caracteristicas = mapeo["tipos"]
            
            # 3. Generar múltiples contrafactuales
            contrafactuales = self._generar_multiple_contrafactuales(
                vector_original=vector_original,
                categoria_objetivo=objetivo_categoria,
                limites=limites,
                n_contrafactuales=n_contrafactuales,
                max_cambios=max_cambios,
                caracteristicas_originales=caracteristicas_actuales  # ✅ NUEVO
            )
            
            if not contrafactuales:
                logger.warning("⚠️ No se generaron contrafactuales, usando método simple")
                return self._generar_contrafactual_simple(
                    caracteristicas_actuales, categoria_actual, objetivo_categoria
                )
            
            # 4. Evaluar y filtrar contrafactuales
            contrafactuales_evaluados = self._evaluar_contrafactuales(
                contrafactuales, vector_original, caracteristicas_actuales
            )
            
            # 5. Seleccionar el mejor
            mejor_contrafactual = self._seleccionar_mejor_contrafactual(
                contrafactuales_evaluados
            )
            
            # 6. Formatear resultados
            return self._formatear_resultados(
                mejor_contrafactual,
                caracteristicas_actuales,
                categoria_actual,
                puntaje_actual,
                objetivo_categoria
            )
            
        except Exception as error:
            logger.error(f"❌ Error generando contrafactuales: {error}")
            raise ContrafactualError(f"Error en generación de contrafactuales: {error}")
    
    def _preparar_optimizacion(
        self, 
        caracteristicas: Dict, 
        embeddings: Dict
    ) -> Tuple[np.ndarray, List[Tuple], Dict]:
        """
        ✅ CORRECCIÓN 5: Preparación robusta con mapeo explícito
        """
        caracteristicas_numericas = []
        limites = []
        nombres_mapeo = []
        tipos_mapeo = {}
        
        # Ordenar características para consistencia
        caracteristicas_ordenadas = sorted(caracteristicas.items())
        
        for nombre, valor in caracteristicas_ordenadas:
            if isinstance(valor, (int, float)):
                caracteristicas_numericas.append(float(valor))
                nombres_mapeo.append(nombre)
                tipos_mapeo[nombre] = type(valor)
                
                # Definir límites con restricciones de factibilidad
                limite_inferior, limite_superior = self._calcular_limites_factibles(
                    nombre, valor
                )
                limites.append((limite_inferior, limite_superior))
        
        # Agregar embeddings
        vector_embeddings = []
        for cat_nombre, embedding in embeddings.items():
            if isinstance(embedding, list):
                vector_embeddings.extend(embedding)
                # Para embeddings, límites entre -2 y 2 (más amplio que [-1, 1])
                for i in range(len(embedding)):
                    nombres_mapeo.append(f"emb_{cat_nombre}_{i}")
                    tipos_mapeo[f"emb_{cat_nombre}_{i}"] = float
                    limites.append((-2.0, 2.0))
        
        vector_completo = np.array(caracteristicas_numericas + vector_embeddings)
        
        mapeo_info = {
            "nombres": nombres_mapeo,
            "tipos": tipos_mapeo,
            "dimension_numericas": len(caracteristicas_numericas),
            "dimension_embeddings": len(vector_embeddings)
        }
        
        return vector_completo, limites, mapeo_info
    
    def _calcular_limites_factibles(
        self, 
        caracteristica: str, 
        valor_actual: float
    ) -> Tuple[float, float]:
        """✅ NUEVO: Calcula límites respetando restricciones de factibilidad"""
        
        restriccion = self.restricciones_factibilidad.get(caracteristica, {})
        
        # Límite inferior
        if restriccion.get("solo_incremento", False):
            limite_inferior = valor_actual  # No puede decrecer
        elif "min_valor" in restriccion:
            limite_inferior = max(restriccion["min_valor"], valor_actual * 0.5)
        else:
            limite_inferior = max(0, valor_actual * 0.5)
        
        # Límite superior
        if "max_cambio_relativo" in restriccion:
            max_cambio = restriccion["max_cambio_relativo"]
            limite_superior = valor_actual * max_cambio
        else:
            limite_superior = valor_actual * 1.5
        
        return limite_inferior, limite_superior
    
    def _funcion_objetivo(
        self,
        x: np.ndarray,
        vector_original: np.ndarray,
        categoria_objetivo: str,
        caracteristicas_originales: Dict,  # ✅ NUEVO
        peso_distancia: float = 0.3,
        peso_cambios: float = 0.2,
        peso_factibilidad: float = 0.1  # ✅ NUEVO
    ) -> float:
        """
        ✅ CORRECCIÓN 3: Función objetivo con predicción REAL
        """
        try:
            # 1. Distancia al vector original
            distancia = np.linalg.norm(x - vector_original)
            distancia_normalizada = distancia / len(x)
            
            # 2. Número de cambios significativos
            diferencias = np.abs(x - vector_original)
            umbral_cambio = 0.1 * np.abs(vector_original + 1e-10)
            cambios_significativos = np.sum(diferencias > umbral_cambio)
            
            # 3. ✅ CORRECCIÓN: Convertir a características y hacer predicción REAL
            caracteristicas_prediccion = self._vector_a_caracteristicas(
                x, caracteristicas_originales
            )
            
            # ✅ Usar método real del modelo
            try:
                prediccion = self.modelo.predecir_riesgo_simple(caracteristicas_prediccion)
                probabilidad_objetivo = prediccion.get("probabilidades", {}).get(
                    categoria_objetivo, 0
                )
            except Exception as e:
                logger.warning(f"Error en predicción: {e}, usando valor por defecto")
                probabilidad_objetivo = 0.0
            
            # 4. ✅ NUEVO: Penalización por cambios no factibles
            penalizacion_factibilidad = self._calcular_penalizacion_factibilidad(
                caracteristicas_originales,
                caracteristicas_prediccion
            )
            
            # 5. Combinar en función objetivo (minimizar)
            funcion_valor = (
                peso_distancia * distancia_normalizada +
                peso_cambios * (cambios_significativos / len(x)) +
                peso_factibilidad * penalizacion_factibilidad +
                (1 - probabilidad_objetivo)  # Maximizar probabilidad
            )
            
            return funcion_valor
            
        except Exception as e:
            logger.warning(f"Error en función objetivo: {e}")
            return 1000.0  # Penalización alta
    
    def _calcular_penalizacion_factibilidad(
        self,
        caracteristicas_originales: Dict,
        caracteristicas_propuestas: Dict
    ) -> float:
        """✅ NUEVO: Calcula penalización por violar restricciones de factibilidad"""
        penalizacion = 0.0
        
        for nombre, valor_original in caracteristicas_originales.items():
            if nombre not in caracteristicas_propuestas:
                continue
            
            valor_propuesto = caracteristicas_propuestas[nombre]
            
            if nombre in self.restricciones_factibilidad:
                restriccion = self.restricciones_factibilidad[nombre]
                
                # Solo incremento permitido
                if restriccion.get("solo_incremento", False):
                    if valor_propuesto < valor_original:
                        penalizacion += 10.0  # Penalización severa
                
                # Valor mínimo
                if "min_valor" in restriccion:
                    if valor_propuesto < restriccion["min_valor"]:
                        penalizacion += 5.0
                
                # Cambio relativo máximo
                if "max_cambio_relativo" in restriccion and valor_original > 0:
                    cambio_relativo = abs(valor_propuesto - valor_original) / valor_original
                    if cambio_relativo > restriccion["max_cambio_relativo"]:
                        penalizacion += 3.0
        
        return penalizacion
    
    def _generar_multiple_contrafactuales(
        self,
        vector_original: np.ndarray,
        categoria_objetivo: str,
        limites: List[Tuple],
        n_contrafactuales: int = 3,
        max_cambios: int = 3,
        caracteristicas_originales: Dict = None  # ✅ NUEVO
    ) -> List[np.ndarray]:
        """
        ✅ CORRECCIÓN 2: Usar scipy.optimize.differential_evolution REAL
        """
        contrafactuales = []
        
        for i in range(n_contrafactuales):
            try:
                logger.debug(f"Generando contrafactual {i+1}/{n_contrafactuales}")
                
                # ✅ CORRECCIÓN: Usar función REAL de scipy
                resultado = differential_evolution(
                    func=lambda x: self._funcion_objetivo(
                        x, 
                        vector_original, 
                        categoria_objetivo,
                        caracteristicas_originales
                    ),
                    bounds=limites,
                    maxiter=100,
                    popsize=15,
                    seed=42 + i,
                    disp=False,
                    atol=1e-3,
                    tol=1e-3,
                    workers=1,  # No paralelizar para reproducibilidad
                    updating='deferred'  # Mejor para problemas con ruido
                )
                
                if resultado.success:
                    contrafactual = resultado.x
                    contrafactuales.append(contrafactual)
                    logger.debug(
                        f"✅ Contrafactual {i+1} generado: "
                        f"valor_función={resultado.fun:.4f}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Optimización {i+1} no convergió: {resultado.message}"
                    )
                
            except Exception as error:
                logger.warning(f"❌ Error generando contrafactual {i+1}: {error}")
                continue
        
        logger.info(f"✅ Generados {len(contrafactuales)} contrafactuales exitosos")
        return contrafactuales
    
    def _vector_a_caracteristicas(
        self, 
        vector: np.ndarray, 
        caracteristicas_originales: Dict
    ) -> Dict:
        """
        ✅ CORRECCIÓN 5: Conversión robusta usando mapeo explícito
        """
        caracteristicas = {}
        
        if not self.mapeo_indices_caracteristicas:
            logger.warning("⚠️ Mapeo no inicializado, usando características originales")
            return caracteristicas_originales.copy()
        
        for i, nombre in enumerate(self.mapeo_indices_caracteristicas):
            # Solo procesar características numéricas (no embeddings)
            if nombre.startswith("emb_"):
                continue
            
            if i < len(vector):
                valor = vector[i]
                
                # Aplicar tipo correcto
                tipo_original = self.tipos_caracteristicas.get(nombre, float)
                if tipo_original == int or nombre in [
                    "meses_operacion", "empleados_directos", "empleados_indirectos"
                ]:
                    caracteristicas[nombre] = int(round(max(0, valor)))
                else:
                    caracteristicas[nombre] = max(0.0, float(valor))
        
        # Completar con características originales faltantes
        for nombre, valor in caracteristicas_originales.items():
            if nombre not in caracteristicas:
                caracteristicas[nombre] = valor
        
        return caracteristicas
    
    def _validar_factibilidad_cambios(
        self, 
        cambios: List[CambioContrafactual]
    ) -> bool:
        """✅ NUEVO: Valida que los cambios sean factibles"""
        for cambio in cambios:
            restriccion = self.restricciones_factibilidad.get(cambio.caracteristica, {})
            
            # Solo incremento
            if restriccion.get("solo_incremento", False):
                if cambio.valor_contrafactual < cambio.valor_original:
                    cambio.factible = False
                    return False
            
            # Valor mínimo
            if "min_valor" in restriccion:
                if cambio.valor_contrafactual < restriccion["min_valor"]:
                    cambio.factible = False
                    return False
            
            # Cambio relativo máximo
            if "max_cambio_relativo" in restriccion and cambio.valor_original > 0:
                cambio_rel = abs(
                    cambio.valor_contrafactual - cambio.valor_original
                ) / cambio.valor_original
                if cambio_rel > restriccion["max_cambio_relativo"]:
                    cambio.factible = False
                    return False
            
            cambio.factible = True
        
        return True
    
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
                    contrafactual, caracteristicas_originales
                )
                
                # Hacer predicción REAL
                prediccion = self.modelo.predecir_riesgo_simple(caracteristicas_contrafactual)
                
                # Calcular cambios
                cambios = self._calcular_cambios(
                    caracteristicas_originales, caracteristicas_contrafactual
                )
                
                # ✅ Validar factibilidad
                factible = self._validar_factibilidad_cambios(cambios)
                
                # Crear escenario
                escenario = EscenarioContrafactual(
                    cambios=cambios[:3],
                    categoria_original=caracteristicas_originales.get(
                        "categoria_riesgo", "DESCONOCIDA"
                    ),
                    categoria_contrafactual=prediccion.get("categoria_riesgo", "DESCONOCIDA"),
                    puntaje_original=caracteristicas_originales.get("puntaje_riesgo", 0),
                    puntaje_contrafactual=prediccion.get("puntaje_riesgo", 0),
                    mejora_puntaje=abs(
                        caracteristicas_originales.get("puntaje_riesgo", 0) - 
                        prediccion.get("puntaje_riesgo", 0)
                    ),
                    probabilidad_exito=self._calcular_probabilidad_exito(cambios),
                    distancia_original=float(np.linalg.norm(contrafactual - vector_original)),
                    viabilidad=self._calcular_viabilidad(cambios),
                    factible=factible  # ✅ NUEVO
                )
                
                escenarios.append(escenario)
                
            except Exception as error:
                logger.warning(f"⚠️ Error evaluando contrafactual {idx}: {error}")
                continue
        
        # Filtrar solo escenarios factibles
        escenarios_factibles = [e for e in escenarios if e.factible]
        
        if not escenarios_factibles:
            logger.warning("⚠️ No hay escenarios factibles, retornando todos")
            return escenarios
        
        logger.info(
            f"✅ {len(escenarios_factibles)}/{len(escenarios)} escenarios factibles"
        )
        return escenarios_factibles
    
    # ... (resto de métodos sin cambios significativos)
    
    def _determinar_categoria_objetivo(self, categoria_actual: str) -> str:
        """Determina la categoría objetivo para mejora"""
        mapeo_mejora = {
            "MUY_ALTO": "ALTO",
            "ALTO": "MEDIO",
            "MEDIO": "BAJO",
            "BAJO": "MUY_BAJO",
            "MUY_BAJO": "MUY_BAJO"
        }
        return mapeo_mejora.get(categoria_actual, "BAJO")
    
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
                
                if self._es_cambio_significativo(valor_original, valor_contrafactual):
                    cambio = CambioContrafactual(
                        caracteristica=caracteristica,
                        valor_original=valor_original,
                        valor_contrafactual=valor_contrafactual,
                        impacto=self._calcular_impacto(
                            caracteristica, valor_original, valor_contrafactual
                        ),
                        dificultad=self.dificultades_caracteristicas.get(
                            caracteristica, "MEDIA"
                        ),
                        accion_concreta=self._generar_accion_concreta(
                            caracteristica, valor_original, valor_contrafactual
                        ),
                        tiempo_estimado=self._estimar_tiempo(
                            caracteristica, valor_original, valor_contrafactual
                        ),
                        costo_estimado=self._estimar_costo(
                            caracteristica, valor_original, valor_contrafactual
                        ),
                        factible=True  # Se validará después
                    )
                    cambios.append(cambio)
        
        # Ordenar por impacto descendente
        cambios.sort(key=lambda x: x.impacto, reverse=True)
        
        return cambios
    
    def _es_cambio_significativo(self, original: any, contrafactual: any) -> bool:
        """Determina si un cambio es significativo"""
        if isinstance(original, (int, float)) and isinstance(contrafactual, (int, float)):
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
            "meses_operacion": f"Operar durante {int(valor_contrafactual - valor_original)} meses adicionales",
            "empleados_directos": f"Contratar {int(max(0, valor_contrafactual - valor_original))} empleados adicionales",
            "ingresos_mensuales_promedio": f"Incrementar ingresos mensuales a ${valor_contrafactual:,.0f} COP",
            "capital_trabajo": f"Aumentar capital de trabajo a ${valor_contrafactual:,.0f} COP",
            "experiencia_total": f"Acumular {int(valor_contrafactual)} meses de experiencia en el sector",
        }
        
        return acciones.get(
            caracteristica, 
            f"Modificar {caracteristica.replace('_', ' ')} de {valor_original} a {valor_contrafactual}"
        )
    
    def _estimar_tiempo(self, caracteristica: str, valor_original: any, valor_contrafactual: any) -> str:
        """Estima el tiempo necesario para el cambio"""
        dificultad = self.dificultades_caracteristicas.get(caracteristica, "MEDIA")
        tiempos = {
            "BAJA": "CORTO",
            "MEDIA": "MEDIO",
            "ALTA": "LARGO",
            "MUY_ALTA": "MUY_LARGO"
        }
        return tiempos.get(dificultad, "MEDIO")
    
    def _estimar_costo(self, caracteristica: str, valor_original: any, valor_contrafactual: any) -> float:
        """Estima el costo del cambio"""
        dificultad = self.dificultades_caracteristicas.get(caracteristica, "MEDIA")
        costo_base = self.costos_cambio.get(dificultad, 3)
        
        if isinstance(valor_original, (int, float)) and isinstance(valor_contrafactual, (int, float)):
            if valor_original == 0:
                factor = min(3.0, abs(valor_contrafactual) / 10)
            else:
                factor = min(3.0, abs(valor_contrafactual - valor_original) / abs(valor_original))
            
            return costo_base * factor
        
        return costo_base
    
    def _calcular_probabilidad_exito(self, cambios: List[CambioContrafactual]) -> float:
        """Calcula la probabilidad de éxito"""
        if not cambios:
            return 0.0
        
        probabilidades_dificultad = {
            "BAJA": 0.9,
            "MEDIA": 0.7,
            "ALTA": 0.4,
            "MUY_ALTA": 0.2
        }
        
        probabilidades = []
        for cambio in cambios:
            if not cambio.factible:  # ✅ Considerar factibilidad
                return 0.0
            
            probabilidad = probabilidades_dificultad.get(cambio.dificultad, 0.5)
            probabilidad_ajustada = probabilidad * (1 - cambio.impacto * 0.3)
            probabilidades.append(probabilidad_ajustada)
        
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
                (1 - min(1.0, escenario.distancia_original / 10)) * 0.1  # 10% proximidad
            )
            escenarios_puntuados.append((puntuacion, escenario))
        
        # Seleccionar el de mayor puntuación
        escenarios_puntuados.sort(key=lambda x: x[0], reverse=True)
        
        return escenarios_puntuados[0][1] if escenarios_puntuados else None
    
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
                "costo_estimado_meses": cambio.costo_estimado,
                "factible": cambio.factible
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
                "distancia_original": escenario.distancia_original,
                "factible": escenario.factible
            },
            "recomendaciones": {
                "cambios_prioritarios": [c["caracteristica"] for c in cambios_formateados[:2]],
                "acciones_inmediatas": [c["accion_concreta"] for c in cambios_formateados[:1]],
                "linea_tiempo_estimada": self._generar_linea_tiempo(escenario.cambios)
            },
            "metadatos": {
                "algoritmo": "DiCE",
                "metodo_optimizacion": "differential_evolution",
                "tiempo_generacion": "variable"
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
                    "accion_concreta": f"Incrementar ingresos a ${ingresos_sugerido:,.0f} COP mensuales",
                    "impacto_estimado": 0.6,
                    "dificultad": "ALTA",
                    "tiempo_estimado": "LARGO",
                    "costo_estimado_meses": 6,
                    "factible": True
                })
            
            if "meses_operacion" in caracteristicas:
                meses_actual = caracteristicas["meses_operacion"]
                meses_sugerido = meses_actual + 12
                
                cambios_sugeridos.append({
                    "caracteristica": "meses_operacion",
                    "valor_actual": meses_actual,
                    "valor_sugerido": meses_sugerido,
                    "accion_concreta": f"Operar durante 12 meses adicionales",
                    "impacto_estimado": 0.4,
                    "dificultad": "BAJA",
                    "tiempo_estimado": "LARGO",
                    "costo_estimado_meses": 12,
                    "factible": True
                })
        
        return {
            "escenario_actual": {
                "categoria_riesgo": categoria_actual
            },
            "escenario_objetivo": {
                "categoria_riesgo": objetivo_categoria
            },
            "cambios_necesarios": cambios_sugeridos,
            "metricas_escenario": {
                "mejora_puntaje": 10.0,
                "probabilidad_exito": 0.5,
                "viabilidad_implementacion": 0.6,
                "factible": True
            },
            "recomendaciones": {
                "cambios_prioritarios": [c["caracteristica"] for c in cambios_sugeridos],
                "acciones_inmediatas": [c["accion_concreta"] for c in cambios_sugeridos[:1]],
                "linea_tiempo_estimada": []
            },
            "metadatos": {
                "algoritmo": "REGLAS_SIMPLES",
                "nota": "Optimización fallida, usando reglas heurísticas"
            }
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
                duracion = self._tiempo_a_meses(tiempo)
                linea_tiempo.append({
                    "periodo": tiempo,
                    "meses_desde_inicio": tiempo_acumulado,
                    "duracion_meses": duracion,
                    "cambios": [
                        {
                            "caracteristica": c.caracteristica,
                            "accion": c.accion_concreta,
                            "dificultad": c.dificultad
                        }
                        for c in cambios_por_tiempo[tiempo]
                    ]
                })
                tiempo_acumulado += duracion
        
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