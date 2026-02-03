# Asistente inteligente para el emprendimiento informal en Colombia

Piloto experimental de un asistente inteligente basado en Machine Learning explicable (XAI)  
Trabajo Fin de Master  
Master Universitario en Inteligencia Artificial  
Universidad Internacional de La Rioja (UNIR)

---
## Descripcion del proyecto

Este repositorio contiene el desarrollo del piloto experimental de un asistente inteligente orientado a apoyar la toma de decisiones de emprendedores informales en Colombia.

El sistema integra un modelo hibrido de Machine Learning basado en LightGBM y representaciones densas mediante embeddings, junto con un modulo de explicabilidad (XAI) que permite comprender y auditar las decisiones del modelo utilizando tecnicas como SHAP y LIME.

El objetivo principal es demostrar la viabilidad tecnica y la utilidad social de aplicar inteligencia artificial explicable en contextos socioeconomicos caracterizados por la informalidad, la escasez de datos estructurados y la necesidad de transparencia algoritimica.

---

## Objetivo general

Disenar e implementar un prototipo funcional de un sistema de recomendacion hibrido y explicable que permita realizar el scoring de riesgos y oportunidades para emprendedores de la economia informal en Colombia, garantizando trazabilidad, equidad y transparencia en la toma de decisiones.

---

## Metodologia

El proyecto se desarrollo siguiendo un enfoque de Diseno y Desarrollo, complementado con una fase de piloto experimental, alineado con los principios del Design Science Research.

Las principales fases del trabajo incluyen:

- Analisis y comprension del problema de la economia informal en Colombia  
- Integracion y preprocesamiento de datos no tradicionales  
- Ingenieria de caracteristicas y control de data leakage  
- Entrenamiento de modelos de Machine Learning  
- Balanceo de clases mediante tecnicas como SMOTE y CTGAN  
- Implementacion de un modelo hibrido LightGBM con embeddings  
- Integracion de tecnicas de explicabilidad SHAP y LIME  
- Evaluacion del modelo con metricas de desempeno y equidad  
- Gestion del ciclo de vida del modelo mediante practicas de MLOps  

---

## Arquitectura del sistema

El asistente inteligente se estructura bajo una arquitectura modular de tres capas:

- Capa de interfaz  
- Capa de servicios backend desarrollada con FastAPI  
- Nucleo de inteligencia artificial  

El nucleo de IA incorpora el modelo de clasificacion hibrido, el modulo de explicabilidad (XAI) y el pipeline de MLOps para entrenamiento, versionado y monitoreo del modelo.

---

Modelo de Machine Learning que predice la probabilidad de que un micronegocio colombiano logre formalizarse, basado en datos del **EMICRON 2024** y la **GEIH 2023** del DANE. El pipeline incluye preprocesamiento exhaustivo, balanceo de clases, modelado con LightGBM, explicabilidad dual (SHAP + LIME), análisis de equidad y monitoreo MLOps.

---

##  Métricas del Modelo Final

| Métrica | Valor |
|---|---|
| Algoritmo | LightGBM + SMOTE |
| Dataset | 68,702 micronegocios |
| ROC-AUC | 0.88 |
| Recall (clase formal) | 72% |
| Variable objetivo | `formalidad_laboral` |

---

## Estructura del Proyecto

```
proyecto/
├── 📂 datos_entrada/                  # Módulos EMICRON 2024 + GEIH 2023 (fuente DANE)
├── 📂 scripts_limpieza/               # Limpieza y EDA por módulo
├── 📂 scripts_modelado/               # Pipeline ML completo
├── 📂 scripts_explicabilidad/         # SHAP, LIME, auditoría
├── 📂 graficas_eda/                   # Visualizaciones exploratorias (eda_*)
├── 📂 graficas_capitulo5/             # Figuras del Capítulo 5 TFM (cap5_*)
├── 📂 documentos/                     # Documentos Word del TFM
└── README.md                          # Este archivo
```

---

## Pipeline ML — 8 Fases (CRISP-DM)

### Fase 1 — Ingesta y Limpieza de Datos

Procesamiento de los **8 módulos EMICRON 2024** del DANE y los **3 módulos GEIH 2023** (12 meses). Cada módulo se limpia de forma independiente: imputación, tipificación, eliminación de duplicados, validación de rangos y creación de variables derivadas.

**Scripts principales:**
- `limpieza_modulo_identificacion.py` — Módulo de Identificación
- `limpieza_caracteristicas.py` — Características del micronegocio
- `limpieza_ventas.py` — Ventas e ingresos
- `limpieza_costos.py` / `limpieza_costos_final.py` — Costos, gastos y activos
- `inclusion_financiera_completo.py` — Inclusión financiera (índices de bancarización, crédito formal/informal)
- `personal_ocupado_completo.py` — Personal ocupado
- `emprendimiento_completo.py` — Emprendimiento
- `tic_completo.py` — TIC (índice de madurez digital)
- `geih_2023_pipeline_completo.py` / `geih_2023_limpieza_completa.py` — GEIH 2023 (12 meses, 3 módulos)

### Fase 2 — Análisis Exploratorio (EDA)

Generación de 30+ visualizaciones por módulo: distribuciones, boxplots, correlaciones, mapas coroplèticos departamentales y relaciones sector-formalidad.

**Graficas generadas:** `eda_*.png`, `eda_caract_*.png`, `eda_costos_*.png`, `eda_ventas_*.png`

**Scripts:**
- `eda_modulo_identificacion.py`
- `eda_caracteristicas.py`
- `eda_costos.py` / `eda_costos_nuevo.py`
- `eda_ventas.py`

### Fase 3 — Fusión de Datasets

Integración de EMICRON 2024 con factores departamentales derivados del GEIH 2023. Resolución de conflictos de tipos de datos en el merge y limpieza del dataset resultante (reducido de 116MB a 20MB mediante eliminación de columnas redundantes).

**Scripts:**
- `01_fusion_emicron_geih.py` — Fusión principal
- `diagnostico_fusion.py` — Validación de la fusión
- `diagnostico_tamano.py` — Optimización de tamaño
- `factores_departamentales_completo.py` — Agregación departamento-sector desde GEIH

### Fase 4 — Detección y Corrección de Data Leakage

Proceso crítico de auditoría: detección de variables que filtran información futura o directamente correlacionadas con la variable objetivo. Cambio de la variable objetivo de `exito_compuesto` a `formalidad_laboral` para eliminar leakage.

**Scripts:**
- `detectar_leakage.py` — Análisis de correlaciones sospechosas
- `eliminar_leakage_definitivo.py` — Eliminación de variables problemáticas
- `fix_variable_objetivo.py` / `corregir_variable_objetivo.py` — Cambio de target
- `limpiar_dataset_ml.py` / `limpiar_dataset_correcto.py` — Dataset final limpio
- `verificar_dataset_ml.py` — Validación post-limpieza

### Fase 5 — Modelado y Balanceo

Entrenamiento de LightGBM con tres estrategias de balanceo comparadas: sin balanceo (baseline), SMOTE y CTGAN. El modelo final usa **SMOTE** por mejor rendimiento en Recall sin degradar la precisión.

**Scripts:**
- `02_modelo_baseline.py` — Modelo sin balanceo
- `02_modelo_regularizado.py` — Modelo con regularización
- `03_modelo_final_formalizacion.py` — Modelo final con SMOTE
- `07_ctgan_rapido.py` — Comparación con CTGAN

**Graficas:**
- `cap5_01_distribucion_target.png` — Desbalance original
- `cap5_02_confusion_baseline.png` — Baseline
- `cap5_03_confusion_smote.png` — Con SMOTE
- `cap5_04_roc_smote.png` — Curva ROC final
- `cap5_05_comparacion_balanceo.png` — SMOTE vs CTGAN vs Baseline

### Fase 6 — Evaluación del Modelo

Métricas completas: ROC-AUC, Precision-Recall, matrices de confusión y análisis de curvas de rendimiento.

**Graficas:**
- `11_confusion_matrix_final.png`
- `12_roc_curve_final.png`
- `13_precision_recall_curve.png`
- `cap5_14_precision_recall.png`
- `cap5_15_confusion_final.png`

### Fase 7 — Análisis de Equidad

Evaluación de sesgo usando el indicador **Disparate Impact** por sector económico. Identificación de sectores con posible discriminación algorítmica.

**Scripts:**
- `06_analisis_equidad.py`

**Graficas:**
- `cap5_12_equidad_sectorial.png`
- `09_analisis_equidad.png`

### Fase 8 — Explicabilidad y Auditoría (XAI)

Explicabilidad dual con **SHAP** (global) y **LIME** (local), validación cruzada entre ambos métodos, y monitoreo de drift del modelo.

**Scripts:**
- `04_analisis_shap.py` / `04_shap_explicabilidad.py` — SHAP completo
- `09_lime.py` — LIME con 3 casos explicados
- `08_mlops.py` — MLOps con MLflow + drift detection
- `generar_shap_plots.py` — Generación de SHAP Summary y Bar Plot

**Graficas:**
- `14_shap_summary_plot.png` / `cap5_06_shap_summary.png` — Summary Plot (detalle por muestra)
- `15_shap_bar_plot.png` / `cap5_07_shap_barplot.png` — Bar Plot (importancia global)
- `cap5_08_shap_dependence.png` — Dependence plots top 3 variables
- `cap5_09_shap_waterfall.png` — Waterfall plot
- `cap5_10_lime_casos.png` — LIME: 3 casos explicados
- `cap5_11_shap_lime_comparacion.png` — Triangulación SHAP vs LIME
- `cap5_13_drift_monitoring.png` — Monitoreo de drift
- `fase8_explicabilidad_SHAP_LIME.png` — Infografía Fase 8

---

## Top 10 Variables por Importancia SHAP

| Rank | Variable | SHAP medio | Efecto |
|:---:|---|:---:|---|
| 1 | `activo_intangibles` | 1.45 | ↑ Formal — Protección de propiedad intelectual incentiva formalización |
| 2 | `local_vivienda` | 1.41 | ↓ Informal — Menor escala y visibilidad; único factor negativo del top 3 |
| 3 | `antiguedad_negocio` | 1.22 | ↑ Formal — Experiencia acumulada facilita los procesos |
| 4 | `credito_proveedores` | 0.98 | ↑ Formal — Requiere documentación, genera ciclo virtuoso |
| 5 | `sector_comercio` | 0.87 | ↑ Formal — Mayor presión regulatoria y acceso a programas |
| 6 | `educacion_propietario` | 0.82 | ↑ Formal — Conoce beneficios legales y mecanismos |
| 7 | `resiliencia_financiera` | 0.76 | ↑ Formal — Absorbe costos iniciales de formalización |
| 8 | `acceso_internet` | 0.71 | ↑ Formal — Facilita trámites electrónicos |
| 9 | `inventarios` | 0.64 | ↑ Formal — Operación estructurada requiere control formal |
| 10 | `tarjeta_credito` | 0.59 | ↑ Formal — Integración al sistema financiero |

> **Validación:** Los top 3 predictores coinciden en SHAP y LIME (triangulación metodológica confirmada).

---

##  Documentos Generados

| Documento | Descripción |
|---|---|
| `Capitulo_5_TFM_COMPLETO.docx` | Capítulo 5 completo del TFM (desarrollo y resultados experimentales) |
| `Capitulo_5_TFM_REFERENCIAS_REALES.docx` | Versión con referencias auditadas a archivos reales |
| `Explicacion_SHAP_Summary_Bar_Plot.docx` | Explicación detallada en español de ambas gráficas SHAP |
| `Explicabilidad_SHAP_LIME_Completo.docx` | Documento técnico SHAP vs LIME |
| `ANEXO_Visualizaciones_Cap5.docx` | Anexo con todas las visualizaciones del Capítulo 5 |
| `Analisis_Completo_TFM_FINAL_v3.docx` | Análisis completo del TFM (versión final) |
| `seccion_3.3_metodologia_CONCISA.txt` | Sección 3.3 metodología (versión concisa para Cap. 3) |
| `seccion_3.3_metodologia_ajustada.txt` | Sección 3.3 metodología (versión detallada) |
| `GRAFICAS_CAPITULO_5.md` | Guía de nomenclatura y ubicación de gráficas |
| `MAPEO_GRAFICAS_DOCUMENTO.md` | Mapeo gráficas → secciones del documento |

---

##  Hallazgos Principales y Palancas de Política Pública

**1. Tres variables dominan el modelo.** `activo_intangibles`, `local_vivienda` y `antiguedad_negocio` contienen la mayor parte de la información predictiva. Hay un salto notable entre el tercer predictor (1.22) y el cuarto (0.98).

**2. Patrones económicamente coherentes.** Cada variable identificada tiene una explicación económica sólida: los activos intangibles requieren protección legal, la antigüedad permite aprender procesos, el crédito exige documentación. El modelo no aprende patrones espurios.

**3. `local_vivienda` es un factor de riesgo claro.** Es la única variable del top 3 con efecto negativo. Los micronegocios que operan desde la vivienda necesitan atención especial: programas que faciliten la transición a espacios comerciales o que permitan la formalización desde la vivienda.

**4. Palancas modificables por intervención pública:**
- **Crédito de proveedores** → Garantías gubernamentales
- **Acceso a internet** → Programas de conectividad rural
- **Educación del propietario** → Programas de capacitación empresarial

---

## Tecnologías

| Área | Herramientas |
|---|---|
| Datos | Python, Pandas, NumPy, DANE (EMICRON 2024, GEIH 2023) |
| Modelado | LightGBM, Scikit-learn, SMOTE (imblearn), CTGAN |
| Explicabilidad | SHAP, LIME |
| MLOps | MLflow, drift detection |
| Visualización | Matplotlib, Seaborn |
| Documentación | python-docx |

---

## Contexto Académico

Este proyecto es parte del **Trabajo Final de Máster (TFM)** sobre desarrollo de un asistente inteligente para emprendimiento informal en Colombia. El pipeline ML forma el núcleo del **Capítulo 5** (Desarrollo y Resultados Experimentales), siguiendo la metodología **CRISP-DM** adaptada al contexto de políticas públicas.

- **Fuentes de datos:** DANE Colombia — Encuesta Micronegociosa (EMICRON 2024) y Gran Encuesta Integrada de Hogares (GEIH 2023)
- **Metodología:** CRISP-DM con 8 fases adaptadas
- **Enfoque:** Predicción retrospectiva + explicabilidad para decisiones de política pública
