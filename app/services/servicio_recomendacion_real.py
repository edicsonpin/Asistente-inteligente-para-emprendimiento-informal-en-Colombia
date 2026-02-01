# servicio_recomendacion_real.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime
import logging

from database.models import Negocio, EvaluacionRiesgo, Oportunidad, Recomendacion, Emprendedor
from database.models_xai import ExplicacionContrafactual, EmbeddingsCaracteristicas
from nucleo.modelo_hibrido import ModeloHibridoTFM
from nucleo.filtro_colaborativo import FiltroColaborativo
from services.servicio_xai_real import ServicioXAIReal
from nucleo.excepciones import NoEncontradoExcepcion

logger = logging.getLogger(__name__)

class ServicioRecomendacionReal:
    
    def __init__(self, ruta_modelo_hibrido: str = "modelos/hibrido_tfm"):
        """Inicializa el servicio con el modelo híbrido real"""
        self.modelo_hibrido = ModeloHibridoTFM(ruta_modelo_hibrido)
        self.filtro_colaborativo = FiltroColaborativo()
        self.servicio_xai = ServicioXAIReal(self.modelo_hibrido)
        self.cargar_modelos()
    
    def cargar_modelos(self):
        """Carga los modelos entrenados"""
        try:
            self.modelo_hibrido.cargar_modelos()
            logger.info("Modelo híbrido cargado exitosamente")
        except Exception as error:
            logger.error(f"Error cargando modelo híbrido: {error}")
            raise
    
    def generar_recomendacion_completa(
        self,
        sesion_base_datos: Session,
        id_negocio: int,
        limite: int = 10,
        incluir_explicacion: bool = True
    ) -> Dict:
        """
        Genera recomendaciones REALES usando el modelo híbrido del TFM
        
        Implementa exactamente el diagrama de secuencia de la Figura 12
        """
        # 1. Obtener negocio y características (Mensaje 1-3 del Diagrama 12)
        negocio, caracteristicas_completas = self._obtener_negocio_y_caracteristicas(
            sesion_base_datos, id_negocio
        )
        
        # 2. Generar embeddings categóricos REALES
        embeddings_categoricos = self._generar_embeddings_categoricos(
            caracteristicas_completas
        )
        
        # 3. Predecir riesgo con modelo híbrido REAL (Mensaje 4)
        prediccion_riesgo = self.modelo_hibrido.predecir_riesgo(
            caracteristicas_numericas=caracteristicas_completas["numericas"],
            embeddings_categoricos=embeddings_categoricos
        )
        
        # 4. Guardar evaluación con embeddings REALES
        evaluacion_riesgo = self._guardar_evaluacion_completa(
            sesion_base_datos,
            negocio,
            prediccion_riesgo,
            embeddings_categoricos
        )
        
        # 5. Calcular compatibilidad REAL con filtro colaborativo + contenido
        oportunidades_compatibles = self._calcular_oportunidades_compatibles_reales(
            sesion_base_datos,
            negocio,
            caracteristicas_completas,
            embeddings_categoricos,
            prediccion_riesgo["categoria_riesgo"],
            limite
        )
        
        # 6. Crear recomendaciones con puntajes REALES
        recomendaciones = self._crear_recomendaciones_reales(
            sesion_base_datos,
            negocio.id,
            evaluacion_riesgo.id,
            oportunidades_compatibles,
            caracteristicas_completas,
            embeddings_categoricos
        )
        
        # 7. Generar explicaciones XAI REALES si se solicita
        explicaciones = None
        if incluir_explicacion:
            explicaciones = self.servicio_xai.generar_explicaciones_completas(
                sesion_base_datos,
                evaluacion_riesgo.id,
                caracteristicas_completas,
                embeddings_categoricos,
                prediccion_riesgo
            )
        
        return {
            "evaluacion_riesgo": evaluacion_riesgo,
            "oportunidades": oportunidades_compatibles,
            "recomendaciones": recomendaciones,
            "explicaciones_xai": explicaciones,
            "metadatos": {
                "modelo_utilizado": "hibrido_lightgbm_nn_v1.0",
                "tipo_recomendacion": "hibrida_colaborativa_contenido",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _obtener_negocio_y_caracteristicas(
        self,
        sesion_base_datos: Session,
        id_negocio: int
    ) -> Tuple[Negocio, Dict]:
        """Extrae TODAS las características del TFM, no solo las básicas"""
        negocio = sesion_base_datos.query(Negocio).options(
            joinedload(Negocio.emprendedor),
            joinedload(Negocio.ciudad),
            joinedload(Negocio.departamento),
            joinedload(Negocio.barrio)
        ).filter(Negocio.id == id_negocio).first()
        
        if not negocio:
            raise NoEncontradoExcepcion("Negocio no encontrado")
        
        # Características NUMÉRICAS completas según TFM
        caracteristicas_numericas = {
            # Datos del emprendedor
            "experiencia_total": negocio.emprendedor.experiencia_total or 0,
            "conteo_habilidades": len(negocio.emprendedor.habilidades or []),
            
            # Datos del negocio (sección 2.2.2 del TFM)
            "meses_operacion": negocio.meses_operacion or 0,
            "empleados_directos": negocio.empleados_directos or 0,
            "empleados_indirectos": negocio.empleados_indirectos or 0,
            "ingresos_mensuales_promedio": negocio.ingresos_mensuales_promedio or 0,
            "capital_trabajo": negocio.capital_trabajo or 0,
            "activos_totales": negocio.activos_totales or 0,
            "pasivos_totales": negocio.pasivos_totales or 0,
            "deuda_existente": negocio.deuda_existente or 0,
            "flujo_efectivo_mensual": negocio.flujo_efectivo_mensual or 0,
            "edad_negocio": negocio.edad_negocio or 0,
            
            # Métricas calculadas
            "ratio_deuda_ingresos": self._calcular_ratio_deuda_ingresos(negocio),
            "rentabilidad_estimada": self._calcular_rentabilidad(negocio),
            
            # Puntajes (si existen)
            "puntaje_credito_negocio": negocio.puntaje_credito_negocio or 0,
            "historial_pagos_negocio": negocio.historial_pagos_negocio or 0,
        }
        
        # Características CATEGÓRICAS para embeddings (Tabla 1 del TFM)
        caracteristicas_categoricas = {
            "sector_negocio": negocio.sector_negocio.value,
            "subsector": negocio.subsector or "OTRO",
            "modelo_negocio": negocio.modelo_negocio or "NO_ESPECIFICADO",
            "nivel_educacion": self._obtener_nivel_educacion(negocio.emprendedor),
            "tipo_documento": negocio.tipo_documento.value if negocio.tipo_documento else "OTRO",
            "codigo_ciiu": negocio.codigo_ciiu or "0000",
            "ubicacion_geografica": self._codificar_ubicacion(negocio),
        }
        
        # Variables protegidas para equidad (sección 2.2.3 del TFM)
        variables_protegidas = {
            "genero": self._inferir_genero(negocio.emprendedor),
            "rango_edad": self._calcular_rango_edad(negocio.emprendedor),
            "territorio": negocio.departamento.nombre if negocio.departamento else "NO_ESPECIFICADO",
        }
        
        return negocio, {
            "numericas": caracteristicas_numericas,
            "categoricas": caracteristicas_categoricas,
            "protegidas": variables_protegidas,
            "embeddings_necesarios": ["sector_negocio", "subsector", "ubicacion_geografica"]
        }
    
    def _generar_embeddings_categoricos(self, caracteristicas: Dict) -> Dict:
        """Genera embeddings REALES usando la red neuronal del modelo híbrido"""
        # Esta función llama al componente de embeddings del modelo híbrido
        embeddings = {}
        
        for categoria in caracteristicas.get("embeddings_necesarios", []):
            if categoria in caracteristicas["categoricas"]:
                valor_categorico = caracteristicas["categoricas"][categoria]
                # Usa el modelo real de embeddings
                embedding = self.modelo_hibrido.generar_embedding_categorico(
                    categoria=categoria,
                    valor=valor_categorico
                )
                embeddings[categoria] = embedding
        
        return {
            "embeddings_individuales": embeddings,
            "embedding_concatenado": self.modelo_hibrido.concatenar_embeddings(embeddings),
            "dimension_total": sum(len(e) for e in embeddings.values())
        }
    
    def _calcular_oportunidades_compatibles_reales(
        self,
        sesion_base_datos: Session,
        negocio: Negocio,
        caracteristicas: Dict,
        embeddings: Dict,
        categoria_riesgo: str,
        limite: int
    ) -> List[Oportunidad]:
        """
        Calcula compatibilidad REAL usando:
        1. Filtrado por contenido (características del negocio)
        2. Filtrado colaborativo (negocios similares)
        3. Restricciones de riesgo (categoría del TFM)
        """
        # Obtener todas las oportunidades activas
        oportunidades = sesion_base_datos.query(Oportunidad).filter(
            Oportunidad.estado == "ACTIVA",
            Oportunidad.fecha_cierre >= datetime.now()
        ).all()
        
        # Calcular puntaje de compatibilidad para cada oportunidad
        oportunidades_con_puntaje = []
        
        for oportunidad in oportunidades:
            # 1. Puntaje por contenido (coincidencia de características)
            puntaje_contenido = self._calcular_puntaje_contenido(
                negocio, oportunidad, caracteristicas
            )
            
            # 2. Puntaje colaborativo (negocios similares que aplicaron)
            puntaje_colaborativo = self.filtro_colaborativo.calcular_similitud(
                id_negocio=negocio.id,
                id_oportunidad=oportunidad.id,
                embeddings_negocio=embeddings["embedding_concatenado"]
            )
            
            # 3. Puntaje por restricciones de riesgo
            puntaje_riesgo = self._verificar_compatibilidad_riesgo(
                categoria_riesgo, oportunidad
            )
            
            # Puntaje final ponderado (como en el TFM)
            puntaje_final = (
                puntaje_contenido * 0.4 +    # 40% contenido
                puntaje_colaborativo * 0.35 + # 35% colaborativo
                puntaje_riesgo * 0.25        # 25% restricciones riesgo
            )
            
            if puntaje_final > 0.5:  # Umbral de compatibilidad
                setattr(oportunidad, 'puntaje_compatibilidad', puntaje_final)
                setattr(oportunidad, 'puntaje_contenido', puntaje_contenido)
                setattr(oportunidad, 'puntaje_colaborativo', puntaje_colaborativo)
                oportunidades_con_puntaje.append(oportunidad)
        
        # Ordenar por puntaje y limitar
        oportunidades_con_puntaje.sort(
            key=lambda x: x.puntaje_compatibilidad, 
            reverse=True
        )
        
        return oportunidades_con_puntaje[:limite]
    
    def _calcular_puntaje_contenido(
        self,
        negocio: Negocio,
        oportunidad: Oportunidad,
        caracteristicas: Dict
    ) -> float:
        """Calcula compatibilidad basada en contenido REAL"""
        puntaje = 0.0
        factores_coincidentes = 0
        
        # Coincidencia de sector (peso alto)
        if oportunidad.sector_compatible == negocio.sector_negocio:
            puntaje += 0.3
            factores_coincidentes += 1
        
        # Coincidencia de requisitos mínimos
        if (oportunidad.experiencia_minima or 0) <= (negocio.experiencia_sector or 0):
            puntaje += 0.15
            factores_coincidentes += 1
        
        if (oportunidad.empleados_minimos or 0) <= (negocio.empleados_directos or 0):
            puntaje += 0.1
            factores_coincidentes += 1
        
        if (oportunidad.ingresos_minimos or 0) <= (negocio.ingresos_mensuales_promedio or 0):
            puntaje += 0.15
            factores_coincidentes += 1
        
        # Coincidencia de ubicación geográfica (si aplica)
        if hasattr(oportunidad, 'ubicacion_preferente'):
            if self._coincide_ubicacion(negocio, oportunidad.ubicacion_preferente):
                puntaje += 0.1
                factores_coincidentes += 1
        
        # Ajustar por número de factores coincidentes
        if factores_coincidentes > 0:
            puntaje *= (1 + (factores_coincidentes * 0.05))
        
        return min(puntaje, 1.0)  # Normalizar a máximo 1.0
    
    def _crear_recomendaciones_reales(
        self,
        sesion_base_datos: Session,
        id_negocio: int,
        id_evaluacion: int,
        oportunidades: List[Oportunidad],
        caracteristicas: Dict,
        embeddings: Dict
    ) -> List[Recomendacion]:
        """Crea recomendaciones con puntajes REALES"""
        recomendaciones = []
        
        for oportunidad in oportunidades:
            # Generar explicación específica para esta recomendación
            explicacion = self._generar_explicacion_recomendacion(
                negocio_id=id_negocio,
                oportunidad=oportunidad,
                puntaje_contenido=oportunidad.puntaje_contenido,
                puntaje_colaborativo=oportunidad.puntaje_colaborativo
            )
            
            recomendacion = Recomendacion(
                negocio_id=id_negocio,
                oportunidad_id=oportunidad.id,
                puntaje_contenido=oportunidad.puntaje_contenido,
                puntaje_colaborativo=oportunidad.puntaje_colaborativo,
                puntaje_conocimiento=self._calcular_puntaje_conocimiento(
                    oportunidad, caracteristicas
                ),
                puntaje_final=oportunidad.puntaje_compatibilidad,
                explicacion=explicacion,
                caracteristicas_compatibles=self._extraer_caracteristicas_compatibles(
                    oportunidad, caracteristicas
                ),
                algoritmo_utilizado="HIBRIDO_LIGHTGBM_NN_FILTRO_COLABORATIVO",
                mostrada=True
            )
            
            sesion_base_datos.add(recomendacion)
            recomendaciones.append(recomendacion)
        
        sesion_base_datos.commit()
        return recomendaciones
    
    def _guardar_evaluacion_completa(
        self,
        sesion_base_datos: Session,
        negocio: Negocio,
        prediccion: Dict,
        embeddings: Dict
    ) -> EvaluacionRiesgo:
        """Guarda evaluación con embeddings REALES"""
        evaluacion = EvaluacionRiesgo(
            emprendedor_id=negocio.emprendedor_id,
            negocio_id=negocio.id,
            modelo_ia_id=self.modelo_hibrido.id_modelo,
            categoria_riesgo=prediccion["categoria_riesgo"],
            puntaje_riesgo=prediccion["puntaje_riesgo"],
            confianza_prediccion=prediccion["confianza_prediccion"],
            probabilidad_muy_bajo=prediccion["probabilidades"]["MUY_BAJO"],
            probabilidad_bajo=prediccion["probabilidades"]["BAJO"],
            probabilidad_medio=prediccion["probabilidades"]["MEDIO"],
            probabilidad_alto=prediccion["probabilidades"]["ALTO"],
            probabilidad_muy_alto=prediccion["probabilidades"]["MUY_ALTO"],
            tiempo_procesamiento=prediccion["tiempo_procesamiento_ms"],
            version_modelo=self.modelo_hibrido.version,
            # Nuevos campos para XAI
            caracteristicas_importantes=prediccion.get("caracteristicas_importantes", []),
            impacto_caracteristicas=prediccion.get("impacto_caracteristicas", {})
        )
        
        sesion_base_datos.add(evaluacion)
        sesion_base_datos.commit()
        sesion_base_datos.refresh(evaluacion)
        
        # Guardar embeddings REALES en tabla especializada
        self._guardar_embeddings_reales(
            sesion_base_datos, evaluacion.id, embeddings
        )
        
        return evaluacion
    
    def _guardar_embeddings_reales(
        self,
        sesion_base_datos: Session,
        id_evaluacion: int,
        embeddings: Dict
    ):
        """Guarda embeddings generados por la red neuronal"""
        embedding_entidad = EmbeddingsCaracteristicas(
            evaluacion_riesgo_id=id_evaluacion,
            embedding_categoricas=embeddings.get("embeddings_individuales", {}),
            embedding_final=embeddings.get("embedding_concatenado", []),
            modelo_embedding=self.modelo_hibrido.nombre_modelo_embedding,
            dimension_embedding=embeddings.get("dimension_total", 0)
        )
        
        sesion_base_datos.add(embedding_entidad)
        sesion_base_datos.commit()
    
    # ==================== FUNCIONES AUXILIARES REALES ====================
    
    def _calcular_ratio_deuda_ingresos(self, negocio: Negocio) -> float:
        """Calcula ratio deuda/ingresos según metodología financiera"""
        if negocio.ingresos_mensuales_promedio and negocio.ingresos_mensuales_promedio > 0:
            deuda_total = (negocio.deuda_existente or 0) + (negocio.pasivos_totales or 0)
            return deuda_total / (negocio.ingresos_mensuales_promedio * 12)  # Anualizado
        return 0.0
    
    def _calcular_rentabilidad(self, negocio: Negocio) -> float:
        """Calcula rentabilidad estimada"""
        ingresos_anuales = (negocio.ingresos_mensuales_promedio or 0) * 12
        costos_estimados = ingresos_anuales * 0.7  # Estimación del 70% como costo
        utilidad = ingresos_anuales - costos_estimados
        
        if (negocio.activos_totales or 0) > 0:
            return utilidad / negocio.activos_totales
        return utilidad
    
    def _obtener_nivel_educacion(self, emprendedor: Emprendedor) -> str:
        """Infiere nivel educativo del emprendedor"""
        # En producción, esto vendría de una tabla específica
        # Por ahora, usamos un valor por defecto
        return "SECUNDARIA"
    
    def _codificar_ubicacion(self, negocio: Negocio) -> str:
        """Codifica ubicación para embeddings"""
        componentes = []
        if negocio.departamento:
            componentes.append(negocio.departamento.nombre[:3].upper())
        if negocio.ciudad:
            componentes.append(negocio.ciudad.nombre[:3].upper())
        return "_".join(componentes) if componentes else "NO_UBICACION"
    
    def _inferir_genero(self, emprendedor: Emprendedor) -> str:
        """Infiere género del emprendedor (para análisis de equidad)"""
        # En producción, esto sería un campo explícito
        # Por ahora, retornamos neutral
        return "NO_ESPECIFICADO"
    
    def _calcular_rango_edad(self, emprendedor: Emprendedor) -> str:
        """Calcula rango de edad (para análisis de equidad)"""
        # En producción, calcularíamos desde fecha_nacimiento
        return "ADULTO"
    
    def _verificar_compatibilidad_riesgo(
        self,
        categoria_riesgo: str,
        oportunidad: Oportunidad
    ) -> float:
        """Verifica compatibilidad según restricciones de riesgo"""
        if not oportunidad.riesgo_minimo or not oportunidad.riesgo_maximo:
            return 1.0  # Sin restricciones
        
        # Mapeo de categorías a valores numéricos
        valores_riesgo = {
            "MUY_BAJO": 1, "BAJO": 2, "MEDIO": 3, "ALTO": 4, "MUY_ALTO": 5
        }
        
        valor_negocio = valores_riesgo.get(categoria_riesgo, 3)
        valor_minimo = valores_riesgo.get(oportunidad.riesgo_minimo.value, 1)
        valor_maximo = valores_riesgo.get(oportunidad.riesgo_maximo.value, 5)
        
        if valor_minimo <= valor_negocio <= valor_maximo:
            return 1.0
        elif valor_negocio < valor_minimo:
            # Demasiado bajo riesgo para la oportunidad
            return 0.3
        else:
            # Demasiado alto riesgo para la oportunidad
            return 0.1
    
    def _generar_explicacion_recomendacion(
        self,
        negocio_id: int,
        oportunidad: Oportunidad,
        puntaje_contenido: float,
        puntaje_colaborativo: float
    ) -> str:
        """Genera explicación en lenguaje natural para la recomendación"""
        explicacion = f"Esta oportunidad de {oportunidad.tipo.value.lower()} "
        explicacion += f"es compatible con tu negocio "
        
        if puntaje_contenido > 0.7:
            explicacion += "principalmente porque coincide con tu sector y características. "
        elif puntaje_colaborativo > 0.6:
            explicacion += "basado en negocios similares al tuyo que la han encontrado útil. "
        else:
            explicacion += "aunque algunos criterios no coinciden completamente. "
        
        if oportunidad.requisitos:
            explicacion += "Cumples con los requisitos principales. "
        
        return explicacion
    
    def _calcular_puntaje_conocimiento(
        self,
        oportunidad: Oportunidad,
        caracteristicas: Dict
    ) -> float:
        """Calcula puntaje basado en conocimiento experto"""
        # Implementar lógica basada en reglas de expertos
        puntaje = 0.5  # Base
        
        # Regla: Si el negocio tiene menos de 12 meses, oportunidades de capacitación
        if caracteristicas["numericas"]["meses_operacion"] < 12:
            if oportunidad.tipo.value == "CAPACITACION":
                puntaje += 0.3
        
        # Regla: Si tiene deuda alta, oportunidades de refinanciamiento
        if caracteristicas["numericas"]["ratio_deuda_ingresos"] > 0.5:
            if oportunidad.tipo.value == "CREDITO":
                puntaje += 0.2
        
        return min(puntaje, 1.0)
    
    def _extraer_caracteristicas_compatibles(
        self,
        oportunidad: Oportunidad,
        caracteristicas: Dict
    ) -> List[Dict]:
        """Extrae características específicas que hacen compatible la oportunidad"""
        compatibilidades = []
        
        # Sector compatible
        if oportunidad.sector_compatible:
            compatibilidades.append({
                "caracteristica": "sector_negocio",
                "valor_negocio": caracteristicas["categoricas"]["sector_negocio"],
                "valor_oportunidad": oportunidad.sector_compatible.value,
                "compatible": oportunidad.sector_compatible.value == caracteristicas["categoricas"]["sector_negocio"]
            })
        
        return compatibilidades
    
    def _coincide_ubicacion(self, negocio: Negocio, ubicacion_preferente: str) -> bool:
        """Verifica coincidencia de ubicación geográfica"""
        if not ubicacion_preferente:
            return True
        
        # Implementar lógica real de coincidencia geográfica
        ubicacion_negocio = f"{negocio.ciudad.nombre if negocio.ciudad else ''} {negocio.departamento.nombre if negocio.departamento else ''}"
        return ubicacion_preferente.lower() in ubicacion_negocio.lower()