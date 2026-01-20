# services/analisis_service.py

import pandas as pd

def analizar_datos_con_spark(pd_ventas):
    """
    Realiza un análisis estadístico utilizando Pandas.
    Devuelve:
    - pd_ventas (o None si no hay datos)
    - un string con el resumen para mostrar en HTML o consola
    """

    if pd_ventas is None or pd_ventas.empty:
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
        
        # Convertir a lista de diccionarios para fácil uso en Jinja
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

        # ---------------------- Estructura de Datos de Retorno ----------------------
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
        return pd_ventas, None
