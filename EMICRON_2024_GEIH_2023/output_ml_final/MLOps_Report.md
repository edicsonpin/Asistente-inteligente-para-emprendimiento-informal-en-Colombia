# REPORTE MLOps - FORMALIZACION DE MICRONEGOCIOS

## 1. TRACKING DE EXPERIMENTO (MLflow)

### Modelo Final
- **Algoritmo:** LightGBM
- **Técnica de Balanceo:** SMOTE
- **Dataset:** EMICRON 2024 (68,702 micronegocios)

### Hiperparámetros
- n_estimators: 200
- learning_rate: 0.03
- max_depth: 6
- num_leaves: 31
- min_child_samples: 50
- reg_alpha: 1.0
- reg_lambda: 1.0

### Métricas de Performance
- **Accuracy:** 0.9445
- **ROC-AUC:** 0.9845
- **Precision:** 0.68
- **Recall:** 0.72
- **F1-Score:** 0.70

### Dataset Split
- Train: 54,961 muestras
- Test: 13,741 muestras
- Features: 84

---

## 2. ANALISIS DE DRIFT

### Resumen
- **Features analizadas:** 83
- **Features con drift significativo:** 0
- **Porcentaje con drift:** 0.0%

### Interpretación
✅ **OK:** No se detectó drift significativo. La distribución de datos es consistente entre train y test.

### Top 5 Features con Mayor Drift

No se detectaron features con drift significativo.

---

## 3. RECOMENDACIONES PARA PRODUCCION

### Monitoreo Continuo
1. **Re-entrenar modelo cada 3 meses** con nuevos datos de EMICRON
2. **Monitorear drift mensualmente** en las top 10 features más importantes
3. **Establecer alertas** cuando drift KS > 0.3 en features críticas

### Pipeline de Actualización
```python
# Pseudocódigo de pipeline de actualización
1. Cargar nuevos datos EMICRON
2. Calcular drift vs modelo actual
3. Si drift > umbral:
   - Re-entrenar modelo
   - Validar métricas
   - Deploy nuevo modelo
4. Actualizar registro MLflow
```

### Umbrales de Alerta
- **KS < 0.1:** Drift bajo - Monitoreo normal
- **KS 0.1-0.3:** Drift medio - Revisar features
- **KS > 0.3:** Drift alto - **Re-entrenar recomendado**

### Métricas de Negocio
- **Precision mínima aceptable:** 0.60 (evitar falsos positivos)
- **Recall mínimo aceptable:** 0.65 (capturar micronegocios formalizables)
- **ROC-AUC mínimo aceptable:** 0.80

---

## 4. HERRAMIENTAS UTILIZADAS

- **MLflow:** Tracking de experimentos y registro de modelos
- **Scipy:** Tests estadísticos de drift (Kolmogorov-Smirnov)
- **LightGBM:** Modelo de gradient boosting
- **SMOTE:** Balanceo de clases

---

## 5. PROXIMOS PASOS

1. Modelo entrenado y validado
2. Drift detectado y documentado
3. ⏳ Integrar con sistema de scoring (API REST)
4. ⏳ Dashboard de monitoreo en tiempo real
5. ⏳ Pipeline de CI/CD para re-entrenamiento automático
6. ⏳ A/B testing de modelos en producción

---

**Generado:** 2026-01-29 15:24:59
**Versión Modelo:** 1.0
