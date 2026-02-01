import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from typing import Dict, Tuple, List
import logging

# Machine Learning
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# Deep Learning
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Embedding, Flatten, Concatenate, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# LightGBM
import lightgbm as lgb

# MLflow
import mlflow
import mlflow.sklearn
import mlflow.keras

logger = logging.getLogger(__name__)

class EntrenadorModeloHibrido:
    def __init__(self, nombre_modelo: str = "lightgbm_hibrido_tfm"):
        self.nombre_modelo = nombre_modelo
        self.escalador = StandardScaler()
        self.codificadores_etiquetas = {}
        self.columnas_caracteristicas = []
        self.columnas_categoricas = []
        self.columnas_numericas = []
        
    def preparar_datos(self, datos_entrenamiento: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Preparar datos para entrenamiento"""
        dataframe = pd.DataFrame(datos_entrenamiento)
        
        # Definir columnas
        self.columnas_numericas = [
            'experiencia_total', 'conteo_habilidades', 'meses_operacion',
            'empleados_directos', 'ingresos_mensuales', 'activos_totales'
        ]
        
        self.columnas_categoricas = ['sector_negocio']
        
        # Manejar valores nulos
        for columna in self.columnas_numericas:
            dataframe[columna] = dataframe[columna].fillna(0)
        for columna in self.columnas_categoricas:
            dataframe[columna] = dataframe[columna].fillna('OTRO')
        
        # Codificar variables categóricas
        for columna in self.columnas_categoricas:
            if columna not in self.codificadores_etiquetas:
                self.codificadores_etiquetas[columna] = LabelEncoder()
            dataframe[columna] = self.codificadores_etiquetas[columna].fit_transform(dataframe[columna])
        
        # Preparar características y objetivo
        X = dataframe[self.columnas_numericas + self.columnas_categoricas]
        y = dataframe['categoria_riesgo']
        
        # Codificar objetivo
        self.codificador_objetivo = LabelEncoder()
        y_codificado = self.codificador_objetivo.fit_transform(y)
        
        self.columnas_caracteristicas = list(X.columns)
        
        return X, y_codificado
    
    def construir_red_neuronal(self, dimensiones_categoricas: Dict) -> Model:
        """Construir la red neuronal para embeddings"""
        
        # Entradas para características categóricas
        entradas_categoricas = []
        embeddings_categoricos = []
        
        for columna_categorica in self.columnas_categoricas:
            dimension_entrada = dimensiones_categoricas[columna_categorica]
            dimension_embedding = min(50, (dimension_entrada + 1) // 2)
            
            capa_entrada = Input(shape=(1,), name=f'entrada_{columna_categorica}')
            capa_embedding = Embedding(
                input_dim=dimension_entrada, 
                output_dim=dimension_embedding, 
                name=f'embedding_{columna_categorica}'
            )(capa_entrada)
            capa_aplanada = Flatten()(capa_embedding)
            
            entradas_categoricas.append(capa_entrada)
            embeddings_categoricos.append(capa_aplanada)
        
        # Entrada para características numéricas
        entrada_numerica = Input(shape=(len(self.columnas_numericas),), name='entrada_numerica')
        capa_densa_numerica = Dense(64, activation='relu')(entrada_numerica)
        capa_densa_numerica = Dropout(0.2)(capa_densa_numerica)
        capa_densa_numerica = Dense(32, activation='relu')(capa_densa_numerica)
        
        # Concatenar todos los embeddings
        if embeddings_categoricos:
            todos_embeddings = embeddings_categoricos + [capa_densa_numerica]
            concatenado = Concatenate()(todos_embeddings)
        else:
            concatenado = capa_densa_numerica
        
        # Capas finales
        densa1 = Dense(128, activation='relu')(concatenado)
        densa1 = Dropout(0.3)(densa1)
        densa2 = Dense(64, activation='relu')(densa1)
        densa2 = Dropout(0.2)(densa2)
        densa3 = Dense(32, activation='relu')(densa2)
        
        # Capa de salida
        salida = Dense(len(self.codificador_objetivo.classes_), activation='softmax', name='salida')(densa3)
        
        # Modelo completo
        todas_entradas = entradas_categoricas + [entrada_numerica]
        modelo = Model(inputs=todas_entradas, outputs=salida)
        
        modelo.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return modelo
    
    def generar_embeddings(self, modelo: Model, X: pd.DataFrame) -> np.ndarray:
        """Generar embeddings usando la red neuronal"""
        # Preparar entradas para el modelo
        entradas_modelo = []
        for columna_categorica in self.columnas_categoricas:
            entradas_modelo.append(X[columna_categorica].values)
        entradas_modelo.append(X[self.columnas_numericas].values)
        
        # Crear modelo para extraer embeddings
        modelo_embedding = Model(
            inputs=modelo.inputs,
            outputs=modelo.layers[-2].output
        )
        
        embeddings = modelo_embedding.predict(entradas_modelo)
        return embeddings
    
    def entrenar_lightgbm(self, X_embeddings: np.ndarray, y: np.ndarray) -> lgb.Booster:
        """Entrenar modelo LightGBM con los embeddings"""
        # Dividir datos
        X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
            X_embeddings, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Parámetros de LightGBM
        parametros = {
            'objective': 'multiclass',
            'num_class': len(self.codificador_objetivo.classes_),
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'max_depth': -1,
            'min_data_in_leaf': 20,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'lambda_l1': 0.1,
            'lambda_l2': 0.1,
            'verbose': -1
        }
        
        # Dataset de LightGBM
        datos_entrenamiento = lgb.Dataset(X_entrenamiento, label=y_entrenamiento)
        datos_validacion = lgb.Dataset(X_prueba, label=y_prueba, reference=datos_entrenamiento)
        
        # Entrenar modelo
        modelo = lgb.train(
            parametros,
            datos_entrenamiento,
            num_boost_round=1000,
            valid_sets=[datos_validacion],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=100)
            ]
        )
        
        return modelo, X_prueba, y_prueba
    
    def evaluar_modelo(self, modelo: lgb.Booster, X_prueba: np.ndarray, y_prueba: np.ndarray) -> Dict:
        """Evaluar el modelo LightGBM"""
        y_prediccion = modelo.predict(X_prueba)
        y_clases_predichas = np.argmax(y_prediccion, axis=1)
        
        metricas = {
            'exactitud': accuracy_score(y_prueba, y_clases_predichas),
            'precision': precision_score(y_prueba, y_clases_predichas, average='weighted'),
            'recall': recall_score(y_prueba, y_clases_predichas, average='weighted'),
            'puntuacion_f1': f1_score(y_prueba, y_clases_predichas, average='weighted'),
            'matriz_confusion': tf.math.confusion_matrix(y_prueba, y_clases_predichas).numpy().tolist()
        }
        
        # Reporte de clasificación detallado
        reporte_clasificacion = classification_report(
            y_prueba, 
            y_clases_predichas, 
            target_names=self.codificador_objetivo.classes_,
            output_dict=True
        )
        metricas['reporte_clasificacion'] = reporte_clasificacion
        
        return metricas
    
    def entrenar_modelo_hibrido(self, datos_entrenamiento: List[Dict]) -> Dict:
        """Método principal para entrenar el modelo híbrido"""
        logger.info("Iniciando entrenamiento del modelo híbrido...")
        
        try:
            # 1. Preparar datos
            X, y = self.preparar_datos(datos_entrenamiento)
            logger.info(f"Datos preparados: {X.shape[0]} muestras, {X.shape[1]} características")
            
            # 2. Dividir datos para red neuronal y LightGBM
            X_entrenamiento, X_temporal, y_entrenamiento, y_temporal = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )
            X_validacion, X_prueba, y_validacion, y_prueba = train_test_split(
                X_temporal, y_temporal, test_size=0.5, random_state=42, stratify=y_temporal
            )
            
            # 3. Construir y entrenar red neuronal
            dimensiones_categoricas = {
                columna: len(self.codificadores_etiquetas[columna].classes_) 
                for columna in self.columnas_categoricas
            }
            
            modelo_red_neuronal = self.construir_red_neuronal(dimensiones_categoricas)
            logger.info("Red neuronal construida")
            
            # Preparar datos para entrenamiento de red neuronal
            entradas_entrenamiento_nn = []
            for columna_categorica in self.columnas_categoricas:
                entradas_entrenamiento_nn.append(X_entrenamiento[columna_categorica].values)
            entradas_entrenamiento_nn.append(X_entrenamiento[self.columnas_numericas].values)
            
            entradas_validacion_nn = []
            for columna_categorica in self.columnas_categoricas:
                entradas_validacion_nn.append(X_validacion[columna_categorica].values)
            entradas_validacion_nn.append(X_validacion[self.columnas_numericas].values)
            
            # Entrenar red neuronal
            parada_temprana = EarlyStopping(patience=10, restore_best_weights=True)
            
            historial_red_neuronal = modelo_red_neuronal.fit(
                entradas_entrenamiento_nn, y_entrenamiento,
                validation_data=(entradas_validacion_nn, y_validacion),
                epochs=100,
                batch_size=32,
                callbacks=[parada_temprana],
                verbose=0
            )
            
            logger.info("Red neuronal entrenada")
            
            # 4. Generar embeddings para todos los datos
            X_embeddings = self.generar_embeddings(modelo_red_neuronal, X)
            logger.info(f"Embeddings generados: {X_embeddings.shape}")
            
            # 5. Entrenar LightGBM con embeddings
            modelo_lightgbm, X_prueba_lgb, y_prueba_lgb = self.entrenar_lightgbm(X_embeddings, y)
            logger.info("Modelo LightGBM entrenado")
            
            # 6. Evaluar modelo completo
            metricas = self.evaluar_modelo(modelo_lightgbm, X_prueba_lgb, y_prueba_lgb)
            logger.info(f"Métricas del modelo: {metricas}")
            
            # 7. Guardar modelos y preprocesadores
            artefactos_modelo = self.guardar_modelos(modelo_red_neuronal, modelo_lightgbm, metricas)
            
            return {
                'estado': 'exito',
                'metricas': metricas,
                'artefactos_modelo': artefactos_modelo,
                'importancia_caracteristicas': dict(zip(
                    [f'embedding_{i}' for i in range(X_embeddings.shape[1])],
                    modelo_lightgbm.feature_importance().tolist()
                )),
                'muestras_entrenamiento': len(datos_entrenamiento),
                'dimension_embedding': X_embeddings.shape[1]
            }
            
        except Exception as error:
            logger.error(f"Error en entrenamiento: {error}")
            return {
                'estado': 'error',
                'error': str(error)
            }
    
    def guardar_modelos(self, modelo_red_neuronal: Model, modelo_lgb: lgb.Booster, metricas: Dict) -> Dict:
        """Guardar modelos y artefactos"""
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        directorio_modelo = f"modelos/{self.nombre_modelo}_{marca_tiempo}"
        
        # Crear directorio
        import os
        os.makedirs(directorio_modelo, exist_ok=True)
        
        # 1. Guardar red neuronal
        ruta_red_neuronal = f"{directorio_modelo}/red_neuronal.h5"
        modelo_red_neuronal.save(ruta_red_neuronal)
        
        # 2. Guardar modelo LightGBM
        ruta_modelo_lightgbm = f"{directorio_modelo}/modelo_lightgbm.txt"
        modelo_lgb.save_model(ruta_modelo_lightgbm)
        
        # 3. Guardar preprocesadores
        ruta_preprocesadores = f"{directorio_modelo}/preprocesadores.pkl"
        with open(ruta_preprocesadores, 'wb') as archivo:
            pickle.dump({
                'escalador': self.escalador,
                'codificadores_etiquetas': self.codificadores_etiquetas,
                'codificador_objetivo': self.codificador_objetivo,
                'columnas_caracteristicas': self.columnas_caracteristicas,
                'columnas_numericas': self.columnas_numericas,
                'columnas_categoricas': self.columnas_categoricas
            }, archivo)
        
        # 4. Guardar métricas
        ruta_metricas = f"{directorio_modelo}/metricas.json"
        with open(ruta_metricas, 'w') as archivo:
            json.dump(metricas, archivo, indent=2)
        
        # 5. Guardar información del modelo
        informacion_modelo = {
            'nombre_modelo': self.nombre_modelo,
            'marca_tiempo': marca_tiempo,
            'directorio_modelo': directorio_modelo,
            'ruta_red_neuronal': ruta_red_neuronal,
            'ruta_lightgbm': ruta_modelo_lightgbm,
            'ruta_preprocesadores': ruta_preprocesadores,
            'ruta_metricas': ruta_metricas
        }
        
        ruta_informacion = f"{directorio_modelo}/informacion_modelo.json"
        with open(ruta_informacion, 'w') as archivo:
            json.dump(informacion_modelo, archivo, indent=2)
        
        return informacion_modelo
    
    def registrar_en_mlflow(self, artefactos_modelo: Dict, metricas: Dict, datos_entrenamiento: List[Dict]):
        """Registrar experimento en MLflow"""
        try:
            mlflow.set_experiment("modelo_hibrido_tfm")
            
            with mlflow.start_run():
                # Registrar parámetros
                mlflow.log_params({
                    'tipo_modelo': 'hibrido_lightgbm_red_neuronal',
                    'muestras_entrenamiento': len(datos_entrenamiento),
                    'caracteristicas_numericas': len(self.columnas_numericas),
                    'caracteristicas_categoricas': len(self.columnas_categoricas)
                })
                
                # Registrar métricas
                mlflow.log_metrics({
                    'exactitud': metricas['exactitud'],
                    'precision': metricas['precision'],
                    'recall': metricas['recall'],
                    'puntuacion_f1': metricas['puntuacion_f1']
                })
                
                # Registrar artefactos
                mlflow.log_artifact(artefactos_modelo['ruta_red_neuronal'])
                mlflow.log_artifact(artefactos_modelo['ruta_lightgbm'])
                mlflow.log_artifact(artefactos_modelo['ruta_preprocesadores'])
                mlflow.log_artifact(artefactos_modelo['ruta_metricas'])
                
                # Registrar modelo de red neuronal
                mlflow.keras.log_model(
                    tf.keras.models.load_model(artefactos_modelo['ruta_red_neuronal']),
                    "red_neuronal"
                )
                
                # Registrar modelo LightGBM
                mlflow.sklearn.log_model(
                    lgb.Booster(model_file=artefactos_modelo['ruta_lightgbm']),
                    "modelo_lightgbm"
                )
                
                logger.info("Modelo registrado en MLflow")
                
        except Exception as error:
            logger.error(f"Error registrando en MLflow: {error}")