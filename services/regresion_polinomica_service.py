import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score
from db import collection

def obtener_datos_ventas_polinomica():
    """Obtiene datos de ventas de MongoDB para regresión polinómica"""
    try:
        # Obtener las últimas 500 ventas
        ventas = list(collection.find(
            {},
            {'_id': 0, 'cantidad': 1, 'total': 1}
        ).limit(500))
        
        if len(ventas) < 10:
            return None, None
        
        # Convertir a arrays
        df = pd.DataFrame(ventas)
        X = df['cantidad'].values.reshape(-1, 1)
        y = df['total'].values
        
        return X, y
    except Exception as e:
        print(f"Error obtener_datos_ventas_polinomica: {e}")
        return None, None

def entrenar_modelo_polinomico(grado=2):
    """Entrena un modelo de regresión polinómica"""
    try:
        X, y = obtener_datos_ventas_polinomica()
        
        if X is None or len(X) < 10:
            return None
        
        # Transformación polinómica
        poly = PolynomialFeatures(degree=grado)
        X_poly = poly.fit_transform(X)
        
        # Entrenar modelo
        modelo = LinearRegression()
        modelo.fit(X_poly, y)
        y_pred = modelo.predict(X_poly)
        
        # Métricas
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        residuales = y - y_pred
        
        # Diagnóstico inteligente
        if r2 < 0.6:
            diagnostico = "El modelo tiene bajo poder explicativo. Probablemente está **subajustando** (underfitting)."
            color_diagnostico = "warning"
        elif 0.6 <= r2 <= 0.95 and rmse > 1:
            diagnostico = "El modelo se ajusta bien a los datos. Hay un **equilibrio razonable** entre sesgo y varianza."
            color_diagnostico = "success"
        elif r2 > 0.95 and rmse < 3:
            diagnostico = "El modelo podría estar **sobreajustando** (overfitting). Ajusta demasiado el ruido."
            color_diagnostico = "danger"
        else:
            diagnostico = "El modelo parece razonablemente ajustado."
            color_diagnostico = "info"
        
        # Generar curva suave para visualización
        X_linea = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
        X_linea_poly = poly.transform(X_linea)
        y_linea = modelo.predict(X_linea_poly)
        
        return {
            'grado': grado,
            'intercepto': float(modelo.intercept_),
            'coeficientes': [float(c) for c in modelo.coef_],
            'rmse': float(rmse),
            'r2': float(r2),
            'x_datos': X.flatten().tolist(),
            'y_datos': y.tolist(),
            'y_pred': y_pred.tolist(),
            'residuales': residuales.tolist(),
            'x_linea': X_linea.flatten().tolist(),
            'y_linea': y_linea.tolist(),
            'num_datos': len(X),
            'diagnostico': diagnostico,
            'color_diagnostico': color_diagnostico
        }
    except Exception as e:
        print(f"Error entrenar_modelo_polinomico: {e}")
        return None
