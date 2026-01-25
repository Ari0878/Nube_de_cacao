import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from db import collection
from datetime import datetime

def obtener_datos_ventas_multiple():
    """Obtiene datos de ventas de MongoDB para regresión múltiple"""
    try:
        # Obtener las últimas 500 ventas
        ventas = list(collection.find(
            {},
            {'_id': 0, 'tipo': 1, 'cantidad': 1, 'total': 1, 'fecha': 1}
        ).limit(500))
        
        if len(ventas) < 5:
            return None, None, None
        
        # Convertir a DataFrame
        df = pd.DataFrame(ventas)
        
        # Codificar tipos de productos
        tipos_unicos = df['tipo'].unique()
        tipo_a_codigo = {tipo: i for i, tipo in enumerate(tipos_unicos)}
        df['tipo_codigo'] = df['tipo'].map(tipo_a_codigo)
        
        # Extraer día de la semana (0=Lunes, 6=Domingo)
        df['dia_semana'] = pd.to_datetime(df['fecha']).dt.dayofweek
        
        # Preparar features: cantidad, tipo_codigo, dia_semana
        X = df[['cantidad', 'tipo_codigo', 'dia_semana']].values
        y = df['total'].values
        
        return X, y, tipo_a_codigo
    except Exception as e:
        print(f"Error obtener_datos_ventas_multiple: {e}")
        return None, None, None

def entrenar_modelo_multiple():
    """Entrena un modelo de regresión lineal múltiple con datos reales de ventas"""
    try:
        X, y, tipo_a_codigo = obtener_datos_ventas_multiple()
        
        if X is None or len(X) < 5:
            return None
        
        # Entrenar modelo
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        # Predicciones
        y_pred = modelo.predict(X)
        
        # Métricas
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        
        # Preparar datos para visualización (limitar para performance)
        num_puntos = min(100, len(X))
        indices = np.linspace(0, len(X)-1, num_puntos, dtype=int)
        
        # Generar superficie 3D para visualización
        # Usar cantidad y tipo_codigo como ejes, dia_semana promedio
        cantidad_range = np.linspace(X[:, 0].min(), X[:, 0].max(), 20)
        tipo_range = np.linspace(X[:, 1].min(), X[:, 1].max(), 20)
        CANT_grid, TIPO_grid = np.meshgrid(cantidad_range, tipo_range)
        dia_promedio = X[:, 2].mean()
        
        # Predecir en la grilla
        Z = modelo.predict(np.column_stack((
            CANT_grid.ravel(), 
            TIPO_grid.ravel(), 
            np.full(CANT_grid.size, dia_promedio)
        )))
        Z = Z.reshape(CANT_grid.shape)
        
        # Mapeo inverso de códigos a nombres
        codigo_a_tipo = {v: k for k, v in tipo_a_codigo.items()}
        
        return {
            'intercepto': float(modelo.intercept_) if not np.isnan(modelo.intercept_) else 0.0,
            'coef_cantidad': float(modelo.coef_[0]) if not np.isnan(modelo.coef_[0]) else 0.0,
            'coef_tipo': float(modelo.coef_[1]) if not np.isnan(modelo.coef_[1]) else 0.0,
            'coef_dia': float(modelo.coef_[2]) if not np.isnan(modelo.coef_[2]) else 0.0,
            'rmse': float(rmse) if not np.isnan(rmse) else 0.0,
            'r2': float(r2) if not np.isnan(r2) else 0.0,
            'cantidad': np.nan_to_num(X[indices, 0]).tolist(),
            'tipo_codigo': np.nan_to_num(X[indices, 1]).tolist(),
            'dia_semana': np.nan_to_num(X[indices, 2]).tolist(),
            'total': np.nan_to_num(y[indices]).tolist(),
            'total_pred': np.nan_to_num(y_pred[indices]).tolist(),
            'grid_cantidad': np.nan_to_num(CANT_grid).tolist(),
            'grid_tipo': np.nan_to_num(TIPO_grid).tolist(),
            'grid_total': np.nan_to_num(Z).tolist(),
            'num_datos': len(X),
            'tipos_disponibles': codigo_a_tipo,
            'tipo_a_codigo': tipo_a_codigo
        }
    except Exception as e:
        print(f"Error entrenar_modelo_multiple: {e}")
        return None

def predecir_total_venta(cantidad, tipo_producto, dia_semana, modelo):
    """Predice el total de una venta basándose en cantidad, tipo y día de la semana"""
    if modelo is None or cantidad <= 0:
        return None
    
    try:
        # Convertir tipo a código
        tipo_codigo = modelo['tipo_a_codigo'].get(tipo_producto, 0)
        
        # Predecir
        total = (modelo['intercepto'] + 
                modelo['coef_cantidad'] * cantidad + 
                modelo['coef_tipo'] * tipo_codigo + 
                modelo['coef_dia'] * dia_semana)
        return float(total)
    except Exception as e:
        print(f"Error predecir_total_venta: {e}")
        return None
