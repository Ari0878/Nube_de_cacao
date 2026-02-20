import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from db import ventas_col   # ✅ CORREGIDO
from datetime import datetime

def obtener_datos_ventas_multiple():
    """Obtiene datos de ventas de MongoDB para regresión múltiple"""
    try:
        ventas = list(ventas_col.find(   # ✅ CORREGIDO
            {},
            {'_id': 0, 'tipo': 1, 'cantidad': 1, 'total': 1, 'fecha': 1}
        ).limit(500))
        
        if len(ventas) < 5:
            return None, None, None
        
        df = pd.DataFrame(ventas)

        # Validar columnas necesarias
        columnas_necesarias = {'tipo', 'cantidad', 'total', 'fecha'}
        if not columnas_necesarias.issubset(df.columns):
            return None, None, None
        
        # Codificar tipos
        tipos_unicos = df['tipo'].unique()
        tipo_a_codigo = {tipo: i for i, tipo in enumerate(tipos_unicos)}
        df['tipo_codigo'] = df['tipo'].map(tipo_a_codigo)

        # Convertir fecha correctamente
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])

        if df.empty:
            return None, None, None

        df['dia_semana'] = df['fecha'].dt.dayofweek

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
        
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        y_pred = modelo.predict(X)

        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)

        num_puntos = min(100, len(X))
        indices = np.linspace(0, len(X)-1, num_puntos, dtype=int)

        cantidad_range = np.linspace(X[:, 0].min(), X[:, 0].max(), 20)
        tipo_range = np.linspace(X[:, 1].min(), X[:, 1].max(), 20)
        CANT_grid, TIPO_grid = np.meshgrid(cantidad_range, tipo_range)
        dia_promedio = X[:, 2].mean()

        Z = modelo.predict(np.column_stack((
            CANT_grid.ravel(), 
            TIPO_grid.ravel(), 
            np.full(CANT_grid.size, dia_promedio)
        )))
        Z = Z.reshape(CANT_grid.shape)

        codigo_a_tipo = {v: k for k, v in tipo_a_codigo.items()}

        return {
            'intercepto': float(modelo.intercept_),
            'coef_cantidad': float(modelo.coef_[0]),
            'coef_tipo': float(modelo.coef_[1]),
            'coef_dia': float(modelo.coef_[2]),
            'rmse': float(rmse),
            'r2': float(r2),
            'cantidad': X[indices, 0].tolist(),
            'tipo_codigo': X[indices, 1].tolist(),
            'dia_semana': X[indices, 2].tolist(),
            'total': y[indices].tolist(),
            'total_pred': y_pred[indices].tolist(),
            'grid_cantidad': CANT_grid.tolist(),
            'grid_tipo': TIPO_grid.tolist(),
            'grid_total': Z.tolist(),
            'num_datos': len(X),
            'tipos_disponibles': codigo_a_tipo,
            'tipo_a_codigo': tipo_a_codigo
        }

    except Exception as e:
        print(f"Error entrenar_modelo_multiple: {e}")
        return None


def predecir_total_venta(cantidad, tipo_producto, dia_semana, modelo):
    """Predice el total de una venta"""
    if modelo is None or cantidad <= 0:
        return None
    
    try:
        tipo_codigo = modelo['tipo_a_codigo'].get(tipo_producto, 0)

        total = (
            modelo['intercepto'] +
            modelo['coef_cantidad'] * cantidad +
            modelo['coef_tipo'] * tipo_codigo +
            modelo['coef_dia'] * dia_semana
        )

        return float(total)

    except Exception as e:
        print(f"Error predecir_total_venta: {e}")
        return None