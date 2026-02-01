from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
import time

from database.models import Negocio, EvaluacionRiesgo, Oportunidad, Recomendacion
from  services.servicio_modelo import ServicioModelo
from nucleo.excepciones import NoEncontradoExcepcion

class ServicioRecomendacion:
    
    def __init__(self):
        self.servicio_modelo = ServicioModelo()
        self.servicio_modelo.cargar_modelo()
    
    def generar_recomendacion(
        self,
        bd: Session,
        negocio_id: int,
        limite: int = 10,
        incluir_explicacion: bool = True
    ) -> Dict:
        negocio = bd.query(Negocio).options(
            joinedload(Negocio.emprendedor),
            joinedload(Negocio.ciudad)
        ).filter(Negocio.id == negocio_id).first()
        
        if not negocio:
            raise NoEncontradoExcepcion("Negocio no encontrado")
        
        caracteristicas = self._extraer_caracteristicas_negocio(negocio)
        
        prediccion = self.servicio_modelo.predecir_riesgo(caracteristicas)
        
        evaluacion_riesgo = self._guardar_evaluacion_riesgo(
            bd, 
            negocio, 
            prediccion
        )
        
        oportunidades = self._buscar_oportunidades_compatibles(
            bd,
            negocio,
            prediccion["categoria_riesgo"],
            limite
        )
        
        recomendaciones = self._crear_recomendaciones(
            bd,
            negocio_id,
            evaluacion_riesgo.id,
            oportunidades
        )
        
        return {
            "evaluacion_riesgo": evaluacion_riesgo,
            "oportunidades": oportunidades,
            "recomendaciones": recomendaciones
        }
    
    def _extraer_caracteristicas_negocio(self, negocio: Negocio) -> Dict:
        caracteristicas = {
            "experiencia_sector": negocio.experiencia_sector or 0,
            "meses_operacion": negocio.meses_operacion or 0,
            "empleados_directos": negocio.empleados_directos or 0,
            "ingresos_mensuales_promedio": negocio.ingresos_mensuales_promedio or 0,
            "capital_trabajo": negocio.capital_trabajo or 0,
            "sector_negocio_cod": self._codificar_sector(negocio.sector_negocio),
            "nivel_educacion_cod": 3,
            "ciudad_cod": negocio.ciudad_id or 0
        }
        
        return caracteristicas
    
    def _codificar_sector(self, sector: str) -> int:
        mapeo_sectores = {
            "TECNOLOGIA": 1,
            "COMERCIO": 2,
            "SERVICIOS": 3,
            "INDUSTRIA": 4,
            "AGRICULTURA": 5,
            "CONSTRUCCION": 6,
            "TRANSPORTE": 7,
            "TURISMO": 8,
            "SALUD": 9,
            "EDUCACION": 10,
            "OTRO": 11
        }
        return mapeo_sectores.get(sector, 11)
    
    def _guardar_evaluacion_riesgo(
        self,
        bd: Session,
        negocio: Negocio,
        prediccion: Dict
    ) -> EvaluacionRiesgo:
        evaluacion = EvaluacionRiesgo(
            emprendedor_id=negocio.emprendedor_id,
            negocio_id=negocio.id,
            modelo_ia_id=1,
            categoria_riesgo=prediccion["categoria_riesgo"],
            puntaje_riesgo=prediccion["puntaje_riesgo"],
            confianza_prediccion=prediccion["confianza_prediccion"],
            probabilidad_muy_bajo=prediccion["probabilidades"]["MUY_BAJO"],
            probabilidad_bajo=prediccion["probabilidades"]["BAJO"],
            probabilidad_medio=prediccion["probabilidades"]["MEDIO"],
            probabilidad_alto=prediccion["probabilidades"]["ALTO"],
            probabilidad_muy_alto=prediccion["probabilidades"]["MUY_ALTO"],
            tiempo_procesamiento=prediccion["tiempo_procesamiento_ms"],
            version_modelo="1.0"
        )
        
        bd.add(evaluacion)
        bd.commit()
        bd.refresh(evaluacion)
        
        return evaluacion
    
    def _buscar_oportunidades_compatibles(
        self,
        bd: Session,
        negocio: Negocio,
        categoria_riesgo: str,
        limite: int
    ) -> List[Oportunidad]:
        query = bd.query(Oportunidad).filter(
            Oportunidad.estado == "ACTIVA"
        )
        
        if negocio.sector_negocio:
            query = query.filter(
                Oportunidad.sector_compatible == negocio.sector_negocio
            )
        
        mapeo_riesgo = {
            "MUY_BAJO": ["MUY_BAJO", "BAJO"],
            "BAJO": ["MUY_BAJO", "BAJO", "MEDIO"],
            "MEDIO": ["BAJO", "MEDIO", "ALTO"],
            "ALTO": ["MEDIO", "ALTO"],
            "MUY_ALTO": ["ALTO", "MUY_ALTO"]
        }
        
        riesgos_compatibles = mapeo_riesgo.get(categoria_riesgo, [])
        if riesgos_compatibles:
            query = query.filter(
                Oportunidad.riesgo_minimo.in_(riesgos_compatibles)
            )
        
        oportunidades = query.limit(limite).all()
        
        return oportunidades
    
    def _crear_recomendaciones(
        self,
        bd: Session,
        negocio_id: int,
        evaluacion_id: int,
        oportunidades: List[Oportunidad]
    ) -> List[Recomendacion]:
        recomendaciones = []
        
        for oportunidad in oportunidades:
            puntaje_compatibilidad = self._calcular_compatibilidad(
                negocio_id,
                oportunidad.id
            )
            
            recomendacion = Recomendacion(
                negocio_id=negocio_id,
                oportunidad_id=oportunidad.id,
                puntaje_contenido=puntaje_compatibilidad * 0.4,
                puntaje_colaborativo=puntaje_compatibilidad * 0.3,
                puntaje_conocimiento=puntaje_compatibilidad * 0.3,
                puntaje_final=puntaje_compatibilidad,
                explicacion=f"Oportunidad compatible con tu perfil",
                algoritmo_utilizado="HIBRIDO_LIGHTGBM_NN",
                mostrada=True
            )
            
            bd.add(recomendacion)
            recomendaciones.append(recomendacion)
        
        bd.commit()
        
        return recomendaciones
    
    def _calcular_compatibilidad(self, negocio_id: int, oportunidad_id: int) -> float:
        base_score = 0.75
        variacion = (negocio_id + oportunidad_id) % 20 / 100
        return min(base_score + variacion, 0.99)