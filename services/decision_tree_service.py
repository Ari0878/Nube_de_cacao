import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, confusion_matrix, classification_report
from db import ventas_col
import os
from dotenv import load_dotenv
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Cargar configuración
load_dotenv()

def obtener_datos_para_arbol():
    """Obtiene datos de ventas para entrenar árbol de decisión"""
    try:
        ventas = list(ventas_col.find(
            {},
            {'_id': 0, 'cantidad': 1, 'total': 1, 'tipo': 1, 'fecha': 1}
        ).limit(500))
        
        if len(ventas) < 10:
            return None, None
        
        df = pd.DataFrame(ventas)
        
        # ✅ CONVERTIR TIPOS DE DATOS
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')
        df['total'] = pd.to_numeric(df['total'], errors='coerce')
        
        # Validar columnas
        if not all(col in df.columns for col in ['cantidad', 'total']):
            return None, None
        
        # Limpiar datos
        df = df.dropna(subset=['cantidad', 'total'])
        df = df[(df['cantidad'] > 0) & (df['total'] > 0)]
        
        if len(df) < 10:
            return None, None
        
        # Crear características
        df['precio_unitario'] = df['total'] / df['cantidad']
        
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df['dia_semana'] = df['fecha'].dt.dayofweek
            df['mes'] = df['fecha'].dt.month
        else:
            df['dia_semana'] = 0
            df['mes'] = 1
        
        return df, None
    
    except Exception as e:
        print(f"Error obtener_datos_para_arbol: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def entrenar_arbol_regresion():
    """Entrena un árbol de decisión para predecir el total de ventas"""
    try:
        df, _ = obtener_datos_para_arbol()
        
        if df is None:
            return None
        
        # Features y target
        X = df[['cantidad', 'precio_unitario', 'dia_semana', 'mes']].values
        y = df['total'].values
        
        # Split datos
        test_size = 0.2
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Entrenar árbol
        max_depth = int(os.getenv('DECISION_TREE_MAX_DEPTH', 10))
        min_samples_split = int(os.getenv('DECISION_TREE_MIN_SAMPLES_SPLIT', 2))
        min_samples_leaf = int(os.getenv('DECISION_TREE_MIN_SAMPLES_LEAF', 1))
        
        arbol = DecisionTreeRegressor(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=42
        )
        
        arbol.fit(X_train, y_train)
        
        # Predicciones
        y_train_pred = arbol.predict(X_train)
        y_test_pred = arbol.predict(X_test)
        
        # Métricas
        rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))
        rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
        r2_train = r2_score(y_train, y_train_pred)
        r2_test = r2_score(y_test, y_test_pred)
        
        # Importancia de features
        feature_names = ['cantidad', 'precio_unitario', 'dia_semana', 'mes']
        feature_importance = list(arbol.feature_importances_)
        
        # Crear pares para el template
        feature_pairs = [
            {'name': name, 'importance': float(imp)} 
            for name, imp in zip(feature_names, feature_importance)
        ]
        
        # Diagnóstico
        if abs(r2_train - r2_test) > 0.2:
            diagnostico = "⚠️ Posible overfitting: La precisión en entrenamiento es mucho mejor que en test"
            color = "warning"
        elif r2_test < 0.5:
            diagnostico = "❌ Modelo con bajo rendimiento: El modelo no explica bien los datos"
            color = "danger"
        elif r2_test > 0.8:
            diagnostico = "✅ Modelo excelente: Las predicciones son muy precisas"
            color = "success"
        else:
            diagnostico = "✓ Modelo aceptable: Buen balance entre sesgo y varianza"
            color = "info"
        
        # Limitación de datos para gráfico
        num_puntos = min(100, len(X_test))
        indices = np.random.choice(len(X_test), num_puntos, replace=False)
        
        return {
            'tipo': 'regresion',
            'max_depth': int(max_depth),
            'min_samples_split': int(min_samples_split),
            'min_samples_leaf': int(min_samples_leaf),
            'rmse_train': float(rmse_train),
            'rmse_test': float(rmse_test),
            'r2_train': float(r2_train),
            'r2_test': float(r2_test),
            'feature_names': feature_names,
            'feature_importance': [float(f) for f in feature_importance],
            'feature_pairs': feature_pairs,
            'y_test': y_test[indices].tolist(),
            'y_pred': y_test_pred[indices].tolist(),
            'num_datos_train': len(X_train),
            'num_datos_test': len(X_test),
            'diagnostico': diagnostico,
            'color_diagnostico': color,
            'num_nodos': arbol.tree_.node_count,
            'profundidad_arbol': arbol.get_depth()
        }
    
    except Exception as e:
        print(f"Error entrenar_arbol_regresion: {e}")
        import traceback
        traceback.print_exc()
        return None


def entrenar_arbol_clasificacion():
    """Entrena un árbol de decisión para clasificar tipos de ventas"""
    try:
        df, _ = obtener_datos_para_arbol()
        
        if df is None or 'tipo' not in df.columns:
            return None
        
        # Codificar tipos
        tipos_unicos = df['tipo'].dropna().unique()
        if len(tipos_unicos) < 2:
            return None
        
        tipo_encoding = {tipo: i for i, tipo in enumerate(tipos_unicos)}
        df['tipo_codigo'] = df['tipo'].map(tipo_encoding)
        
        # Features y target
        X = df[['cantidad', 'precio_unitario', 'dia_semana', 'mes']].values
        y = df['tipo_codigo'].values
        
        # Split datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entrenar árbol
        arbol = DecisionTreeClassifier(
            max_depth=int(os.getenv('DECISION_TREE_MAX_DEPTH', 10)),
            min_samples_split=int(os.getenv('DECISION_TREE_MIN_SAMPLES_SPLIT', 2)),
            min_samples_leaf=int(os.getenv('DECISION_TREE_MIN_SAMPLES_LEAF', 1)),
            random_state=42
        )
        
        arbol.fit(X_train, y_train)
        
        # Predicciones
        y_train_pred = arbol.predict(X_train)
        y_test_pred = arbol.predict(X_test)
        
        # Métricas
        accuracy_train = accuracy_score(y_train, y_train_pred)
        accuracy_test = accuracy_score(y_test, y_test_pred)
        
        # Importancia de features
        feature_names = ['cantidad', 'precio_unitario', 'dia_semana', 'mes']
        feature_importance = list(arbol.feature_importances_)
        
        # Crear pares para el template
        feature_pairs = [
            {'name': name, 'importance': float(imp)} 
            for name, imp in zip(feature_names, feature_importance)
        ]
        
        # Diagnóstico
        if accuracy_test > 0.85:
            diagnostico = "✅ Clasificación excelente: El modelo clasifica muy bien los tipos de venta"
            color = "success"
        elif accuracy_test > 0.70:
            diagnostico = "✓ Clasificación buena: El modelo funciona bien"
            color = "info"
        elif accuracy_test > 0.50:
            diagnostico = "⚠️ Clasificación aceptable: Podría mejorarse"
            color = "warning"
        else:
            diagnostico = "❌ Clasificación pobre: El modelo no funciona bien"
            color = "danger"
        
        return {
            'tipo': 'clasificacion',
            'accuracy_train': float(accuracy_train),
            'accuracy_test': float(accuracy_test),
            'feature_names': feature_names,
            'feature_importance': [float(f) for f in feature_importance],
            'feature_pairs': feature_pairs,
            'clases': {v: k for k, v in tipo_encoding.items()},
            'num_clases': len(tipos_unicos),
            'num_datos_train': len(X_train),
            'num_datos_test': len(X_test),
            'diagnostico': diagnostico,
            'color_diagnostico': color,
            'num_nodos': arbol.tree_.node_count,
            'profundidad_arbol': arbol.get_depth()
        }
    
    except Exception as e:
        print(f"Error entrenar_arbol_clasificacion: {e}")
        import traceback
        traceback.print_exc()
        return None


def predecir_con_arbol(cantidad, precio_unitario, dia_semana=0, mes=1):
    """Usa el árbol de decisión para hacer una predicción"""
    try:
        df, _ = obtener_datos_para_arbol()
        
        if df is None:
            return None
        
        X = df[['cantidad', 'precio_unitario', 'dia_semana', 'mes']].values
        y = df['total'].values
        
        # Entrenar árbol
        arbol = DecisionTreeRegressor(
            max_depth=int(os.getenv('DECISION_TREE_MAX_DEPTH', 10)),
            min_samples_split=int(os.getenv('DECISION_TREE_MIN_SAMPLES_SPLIT', 2)),
            min_samples_leaf=int(os.getenv('DECISION_TREE_MIN_SAMPLES_LEAF', 1)),
            random_state=42
        )
        arbol.fit(X, y)
        
        # Hacer predicción
        X_nuevo = np.array([[cantidad, precio_unitario, dia_semana, mes]])
        prediccion = arbol.predict(X_nuevo)[0]
        
        return {
            'cantidad': float(cantidad),
            'precio_unitario': float(precio_unitario),
            'dia_semana': int(dia_semana),
            'mes': int(mes),
            'total_predicho': float(prediccion)
        }
    
    except Exception as e:
        print(f"Error predecir_con_arbol: {e}")
        return None


def comparar_arboles():
    """Compara los rendimientos de los árboles de regresión y clasificación"""
    try:
        regresion = entrenar_arbol_regresion()
        clasificacion = entrenar_arbol_clasificacion()
        
        return {
            'regresion': regresion,
            'clasificacion': clasificacion
        }
    except Exception as e:
        print(f"Error comparar_arboles: {e}")
        return None
