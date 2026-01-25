import numpy as np
from db import collection

def obtener_datos_ventas():
    """Obtiene datos de ventas de la base de datos para regresión - OPTIMIZADO"""
    try:
        # Limitar a las últimas 500 ventas para velocidad
        ventas = list(collection.find(
            {},
            {'_id': 0, 'cantidad': 1, 'total': 1}
        ).limit(500))
        
        if not ventas or len(ventas) < 2:
            return None, None
        
        # Usar comprensión de listas para mayor eficiencia
        datos = [(v.get('cantidad', 0), v.get('total', 0)) 
                 for v in ventas 
                 if v.get('cantidad', 0) > 0 and v.get('total', 0) > 0]
        
        if len(datos) < 2:
            return None, None
        
        X = np.array([d[0] for d in datos], dtype=np.float32)
        y = np.array([d[1] for d in datos], dtype=np.float32)
        
        return X.reshape(-1, 1), y
    except Exception as e:
        print(f"Error obtener_datos_ventas: {e}")
        return None, None

def entrenar_modelo_regresion():
    """Entrena un modelo de regresión lineal simple - OPTIMIZADO"""
    try:
        X, y = obtener_datos_ventas()
        
        if X is None or len(X) < 2:
            return None
        
        # Usar operaciones vectorizadas de numpy para mayor velocidad
        X_flat = X.flatten()
        x_mean = X_flat.mean()
        y_mean = y.mean()
        
        # Calcular pendiente y intercepto
        numerador = ((X_flat - x_mean) * (y - y_mean)).sum()
        denominador = ((X_flat - x_mean) ** 2).sum()
        
        if denominador == 0:
            return None
        
        pendiente = numerador / denominador
        intercepto = y_mean - pendiente * x_mean
        
        # Predicciones
        y_pred = pendiente * X_flat + intercepto
        
        # Métricas
        residuos = y - y_pred
        rmse = np.sqrt((residuos ** 2).mean())
        mae = np.abs(residuos).mean()
        
        ss_res = (residuos ** 2).sum()
        ss_tot = ((y - y_mean) ** 2).sum()
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Limitar a 100 puntos para el gráfico
        num_puntos = min(100, len(X_flat))
        indices = np.linspace(0, len(X_flat)-1, num_puntos, dtype=int)
        
        return {
            'pendiente': float(pendiente),
            'intercepto': float(intercepto),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2),
            'X': X_flat[indices].tolist(),
            'y': y[indices].tolist(),
            'y_pred': y_pred[indices].tolist(),
            'num_datos': len(X_flat)
        }
    except Exception as e:
        print(f"Error entrenar_modelo_regresion: {e}")
        return None

def predecir_total(cantidad, modelo):
    """Hace una predicción basada en el modelo entrenado"""
    if modelo is None or cantidad <= 0:
        return None
    
    try:
        return float(modelo['pendiente'] * cantidad + modelo['intercepto'])
    except Exception as e:
        print(f"Error predecir_total: {e}")
        return None
