# services/analisis_service.py
import pandas as pd
import db


def analizar_datos_con_spark(pd_ventas=None):
    """
    Realiza un análisis estadístico utilizando Pandas.
    Si no se pasa pd_ventas, lo obtiene directamente de MySQL.
    Devuelve:
    - pd_ventas (o None si no hay datos)
    - un diccionario con el resumen para mostrar en HTML
    """
    
    # Si no se pasó DataFrame, obtenerlo de MySQL
    if pd_ventas is None or pd_ventas.empty:
        try:
            cursor = db.get_cursor()
            if cursor is None:
                print("Error: No hay conexión a la base de datos")
                return None, None
            
            cursor.execute("""
                SELECT id, cliente, tipo, cantidad, total, fecha 
                FROM ventas 
                ORDER BY fecha DESC
            """)
            
            ventas_list = cursor.fetchall()
            
            if not ventas_list:
                return None, None
            
            # Convertir a DataFrame
            pd_ventas = pd.DataFrame(ventas_list)
            
            # Convertir tipos de datos
            if 'cantidad' in pd_ventas.columns:
                pd_ventas['cantidad'] = pd.to_numeric(pd_ventas['cantidad'], errors='coerce')
            if 'total' in pd_ventas.columns:
                pd_ventas['total'] = pd.to_numeric(pd_ventas['total'], errors='coerce')
            if 'fecha' in pd_ventas.columns:
                pd_ventas['fecha'] = pd.to_datetime(pd_ventas['fecha'], errors='coerce')
                
        except Exception as e:
            print(f"Error al obtener datos de MySQL: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    if pd_ventas is None or pd_ventas.empty:
        return None, None

    try:
        # --- MÉTRICAS PRINCIPALES ---
        total_productos = int(pd_ventas['cantidad'].sum()) if 'cantidad' in pd_ventas.columns else 0
        total_ingresos = float(pd_ventas['total'].sum()) if 'total' in pd_ventas.columns else 0.0
        
        precio_promedio = float(
            total_ingresos / total_productos if total_productos > 0 else 0.0
        )

        # ---------------------- Resumen por tipo ----------------------
        if 'tipo' in pd_ventas.columns and 'cantidad' in pd_ventas.columns and 'total' in pd_ventas.columns:
            resumen_data = pd_ventas.groupby('tipo').agg(
                cantidad_total=('cantidad', 'sum'),
                total_ventas=('total', 'sum')
            ).reset_index()
            
            # Convertir a lista de diccionarios para Jinja
            ventas_por_tipo = resumen_data.to_dict('records')
        else:
            ventas_por_tipo = []

        # ---------------------- Tendencias ----------------------
        try:
            if 'tipo' in pd_ventas.columns and 'cantidad' in pd_ventas.columns:
                top_producto = pd_ventas.groupby('tipo')['cantidad'].sum().idxmax()
            else:
                top_producto = "N/A"
        except:
            top_producto = "N/A"
        
        top_cliente = "N/A"
        if 'cliente' in pd_ventas.columns and 'cantidad' in pd_ventas.columns:
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
        import traceback
        traceback.print_exc()
        return pd_ventas, None


def obtener_resumen_ventas():
    """
    Función simplificada que solo retorna el resumen de análisis.
    Útil para la ruta /analisis
    """
    try:
        cursor = db.get_cursor()
        if cursor is None:
            print("Error: No hay conexión a MySQL")
            return None
        
        # Obtener datos directamente
        cursor.execute("""
            SELECT tipo, SUM(cantidad) as cantidad_total, SUM(total) as total_ventas
            FROM ventas 
            GROUP BY tipo
        """)
        
        ventas_por_tipo = cursor.fetchall()
        
        cursor.execute("SELECT SUM(cantidad) as total, SUM(total) as ingresos FROM ventas")
        totals = cursor.fetchone()
        
        if not totals or not totals.get('total'):
            return None
        
        total_productos = int(totals.get('total', 0))
        total_ingresos = float(totals.get('ingresos', 0.0))
        
        # Obtener top producto
        cursor.execute("""
            SELECT tipo, SUM(cantidad) as total 
            FROM ventas 
            GROUP BY tipo 
            ORDER BY total DESC 
            LIMIT 1
        """)
        top_producto_result = cursor.fetchone()
        top_producto = top_producto_result['tipo'] if top_producto_result else "N/A"
        
        # Obtener top cliente
        cursor.execute("""
            SELECT cliente, SUM(cantidad) as total 
            FROM ventas 
            GROUP BY cliente 
            ORDER BY total DESC 
            LIMIT 1
        """)
        top_cliente_result = cursor.fetchone()
        top_cliente = top_cliente_result['cliente'] if top_cliente_result else "N/A"
        
        precio_promedio = total_ingresos / total_productos if total_productos > 0 else 0.0
        
        return {
            "total_productos": total_productos,
            "total_ingresos": total_ingresos,
            "precio_promedio": precio_promedio,
            "ventas_por_tipo": ventas_por_tipo,
            "top_producto": top_producto,
            "top_cliente": top_cliente
        }
        
    except Exception as e:
        print(f"Error en obtener_resumen_ventas: {e}")
        import traceback
        traceback.print_exc()
        return None