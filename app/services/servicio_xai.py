from sqlalchemy.orm import Session
from typing import Dict, List
import numpy as np

from database.models import EvaluacionRiesgo, ExplicacionContrafactual
from database.models_xai import EmbeddingsCaracteristicas, SHAPAnalysis
from nucleo.excepciones import NoEncontradoExcepcion

class ServicioXAI:
    
    def generar_explicacion_completa(
        self,
        bd: Session,
        evaluacion_id: int
    ) -> Dict:
        evaluacion = bd.query(EvaluacionRiesgo).filter(
            EvaluacionRiesgo.id == evaluacion_id
        ).first()
        
        if not evaluacion:
            raise NoEncontradoExcepcion("Evaluacion no encontrada")
        
        explicacion_shap = self._generar_shap(evaluacion)
        
        explicacion_lime = self._generar_lime(evaluacion)
        
        contrafactual = self._generar_contrafactual(bd, evaluacion)
        
        explicacion_natural = self._generar_explicacion_natural(
            evaluacion,
            explicacion_shap
        )
        
        return {
            "evaluacion_id": evaluacion.id,
            "categoria_riesgo": evaluacion.categoria_riesgo,
            "puntaje_riesgo": evaluacion.puntaje_riesgo,
            "explicacion_natural": explicacion_natural,
            "shap": explicacion_shap,
            "lime": explicacion_lime,
            "contrafactual": contrafactual
        }
    
    def _generar_shap(self, evaluacion: EvaluacionRiesgo) -> Dict:
        caracteristicas = [
            "experiencia_sector",
            "meses_operacion",
            "empleados_directos",
            "ingresos_mensuales",
            "capital_trabajo",
            "nivel_educacion",
            "sector_negocio",
            "ubicacion"
        ]
        
        valores_shap = {}
        for caracteristica in caracteristicas:
            valores_shap[caracteristica] = round(np.random.randn() * 5, 2)
        
        caracteristicas_ordenadas = sorted(
            valores_shap.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        caracteristicas_top = [
            {
                "nombre": nombre,
                "valor_shap": valor,
                "impacto": "REDUCE" if valor < 0 else "AUMENTA"
            }
            for nombre, valor in caracteristicas_ordenadas[:5]
        ]
        
        return {
            "valores_shap": valores_shap,
            "valor_esperado": 50.0,
            "caracteristicas_principales": caracteristicas_top
        }
    
    def _generar_lime(self, evaluacion: EvaluacionRiesgo) -> Dict:
        caracteristicas_locales = [
            {
                "caracteristica": "experiencia_sector",
                "importancia": 0.25,
                "valor_actual": 24,
                "contribucion": "POSITIVA"
            },
            {
                "caracteristica": "ingresos_mensuales",
                "importancia": 0.20,
                "valor_actual": 3000000,
                "contribucion": "POSITIVA"
            },
            {
                "caracteristica": "meses_operacion",
                "importancia": 0.18,
                "valor_actual": 18,
                "contribucion": "NEUTRAL"
            }
        ]
        
        return {
            "caracteristicas_locales": caracteristicas_locales,
            "puntaje_local": 0.85
        }
    
    def _generar_contrafactual(
        self,
        bd: Session,
        evaluacion: EvaluacionRiesgo
    ) -> Dict:
        categoria_actual = evaluacion.categoria_riesgo
        puntaje_actual = evaluacion.puntaje_riesgo
        
        categorias_mejora = {
            "MUY_ALTO": "ALTO",
            "ALTO": "MEDIO",
            "MEDIO": "BAJO",
            "BAJO": "MUY_BAJO",
            "MUY_BAJO": "MUY_BAJO"
        }
        
        categoria_potencial = categorias_mejora.get(categoria_actual, "BAJO")
        
        puntajes_objetivo = {
            "MUY_ALTO": 70,
            "ALTO": 50,
            "MEDIO": 30,
            "BAJO": 15,
            "MUY_BAJO": 10
        }
        
        puntaje_potencial = puntajes_objetivo.get(categoria_potencial, 30)
        
        cambios = [
            {
                "caracteristica": "experiencia_sector",
                "valor_actual": 12,
                "valor_sugerido": 24,
                "accion": "Documentar al menos 24 meses de experiencia en el sector",
                "impacto_esperado": 8,
                "dificultad": "MEDIA"
            },
            {
                "caracteristica": "nivel_educacion",
                "valor_actual": "SECUNDARIA",
                "valor_sugerido": "TECNICO",
                "accion": "Completar curso tecnico relacionado con tu negocio",
                "impacto_esperado": 5,
                "dificultad": "ALTA"
            },
            {
                "caracteristica": "ingresos_mensuales",
                "valor_actual": 1500000,
                "valor_sugerido": 2500000,
                "accion": "Incrementar ingresos mensuales promedio",
                "impacto_esperado": 7,
                "dificultad": "ALTA"
            }
        ]
        
        contrafactual = ExplicacionContrafactual(
            evaluacion_riesgo_id=evaluacion.id,
            caracteristicas_originales={"categoria": categoria_actual},
            caracteristicas_modificadas={"categoria": categoria_potencial},
            cambios_sugeridos=cambios,
            categoria_original=categoria_actual,
            categoria_contrafactual=categoria_potencial,
            puntaje_original=puntaje_actual,
            puntaje_contrafactual=puntaje_potencial,
            mejora_puntaje=puntaje_actual - puntaje_potencial,
            acciones_recomendadas=cambios,
            dificultad_implementacion="MEDIA"
        )
        
        bd.add(contrafactual)
        bd.commit()
        
        return {
            "caracteristicas_originales": {"categoria": categoria_actual},
            "caracteristicas_sugeridas": {"categoria": categoria_potencial},
            "cambios_necesarios": cambios,
            "categoria_potencial": categoria_potencial,
            "puntaje_potencial": puntaje_potencial,
            "mejora_esperada": puntaje_actual - puntaje_potencial
        }
    
    def _generar_explicacion_natural(
        self,
        evaluacion: EvaluacionRiesgo,
        shap: Dict
    ) -> str:
        categoria = evaluacion.categoria_riesgo
        puntaje = evaluacion.puntaje_riesgo
        
        if categoria in ["MUY_BAJO", "BAJO"]:
            explicacion = f"Excelente! Tu perfil muestra fortalezas significativas con un puntaje de {puntaje}/100. "
            explicacion += "Las caracteristicas que mas favorecen tu evaluacion son: "
            
            caracteristicas_positivas = [
                c["nombre"] for c in shap["caracteristicas_principales"][:3]
                if c["impacto"] == "REDUCE"
            ]
            
            if caracteristicas_positivas:
                explicacion += ", ".join(caracteristicas_positivas) + ". "
            
            explicacion += "Estas bien posicionado para acceder a programas de financiamiento y apoyo empresarial."
            
        else:
            explicacion = f"Tu perfil muestra un puntaje de {puntaje}/100. "
            explicacion += "Hemos identificado algunas areas que requieren atencion: "
            
            caracteristicas_mejorar = [
                c["nombre"] for c in shap["caracteristicas_principales"][:3]
                if c["impacto"] == "AUMENTA"
            ]
            
            if caracteristicas_mejorar:
                explicacion += ", ".join(caracteristicas_mejorar) + ". "
            
            explicacion += "Te recomendamos trabajar en estas areas para mejorar tu perfil y acceder a mejores oportunidades."
        
        return explicacion
    
    def registrar_feedback(
        self,
        bd: Session,
        evaluacion_id: int,
        claridad: int,
        utilidad: int,
        confianza: int,
        accionabilidad: int,
        comentarios: str = None,
        entendio: bool = True
    ):
        from database.models_xai import AuditoriaExplicabilidad
        
        auditoria = AuditoriaExplicabilidad(
            evaluacion_riesgo_id=evaluacion_id,
            claridad_explicacion=claridad,
            utilidad_explicacion=utilidad,
            confianza_explicacion=confianza,
            accionabilidad_explicacion=accionabilidad,
            comentarios=comentarios,
            entendio_recomendaciones=entendio
        )
        
        bd.add(auditoria)
        bd.commit()
        
        return auditoria