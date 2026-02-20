# services/analisis_service.py

import pandas as pd
from db import ventas_col   # ✅ CORREGIDO

def analizar_datos_con_spark(pd_ventas=None):
    """
    Realiza un análisis estadístico utilizando Pandas.
    Si no se pasa pd_ventas, lo obtiene directamente de MongoDB.
    Devuelve:
    - pd_ventas (o None si no hay datos)
    - un diccionario con el resumen para mostrar en HTML
    """
    
    # Si no se pasó DataFrame, obtenerlo de MongoDB
    if pd_ventas is None or pd_ventas.empty:
        try:
            ventas_list = list(ventas_col.find())   # ✅ CORREGIDO
            if not ventas_list:
                return None, None
            
            # Convertir a DataFrame
            pd_ventas = pd.DataFrame(ventas_list)
        except Exception as e:
            print(f"Error al obtener datos de MongoDB: {e}")
            return None, None

    if pd_ventas.empty:
        return None, None

    try:
        # --- MÉTRICAS PRINCIPALES ---
        total_productos = int(pd_ventas['cantidad'].sum())
        total_ingresos = float(pd_ventas['total'].sum())
        precio_promedio = float(
            total_ingresos / total_productos if total_productos > 0 else 0.0
        )

        # ---------------------- Resumen por tipo ----------------------
        resumen_data = pd_ventas.groupby('tipo').agg(
            cantidad_total=('cantidad', 'sum'),
            total_ventas=('total', 'sum')
        ).reset_index()
        
        ventas_por_tipo = resumen_data.to_dict('records')

        # ---------------------- Tendencias ----------------------
        try:
            top_producto = pd_ventas.groupby('tipo')['cantidad'].sum().idxmax()
        except:
            top_producto = "N/A"
        
        top_cliente = "N/A"
        if 'cliente' in pd_ventas.columns:
            try:
                top_cliente = pd_ventas.groupby('cliente')['cantidad'].sum().idxmax()
            except:
                top_cliente = "N/A"

        datos_analisis = {
            "total_productos": total_productos,
            "total_ingresos": total_ingresos,
            "precio_promedio": precio_promedio,
            "ventas_por_tipo": ventas_por_tipo,
            "top_producto": top_producto,
            "top_cliente": top_cliente
        }

        return pd_ventas, datos_analisis

    except Exception as e:
        print(f"Error en analisis_service: {e}")
        import traceback
        traceback.print_exc()
        return pd_ventas, None


def obtener_resumen_ventas():
    """
    Función simplificada que solo retorna el resumen de análisis.
    Útil para la ruta /analisis
    """
    _, resumen = analizar_datos_con_spark()
    return resumen