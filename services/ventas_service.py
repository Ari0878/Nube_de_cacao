# services/ventas_service.py
from datetime import datetime
import pandas as pd
import db
from spark_session import get_spark

# Spark Imports
from pyspark.sql.functions import sum, lit
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    FloatType,
)

# Columnas necesarias
COLUMNAS_FIJAS = ["id", "cliente", "tipo", "cantidad", "total", "fecha"]

# --- Esquema Spark ---
schema = StructType([
    StructField("id", StringType(), True),
    StructField("cliente", StringType(), True),
    StructField("tipo", StringType(), True),
    StructField("cantidad", IntegerType(), True),
    StructField("total", FloatType(), True),
    StructField("fecha", StringType(), True),
])


def normalizar_df(df):
    """Asegura que el DataFrame tenga todas las columnas necesarias"""
    for col_name in COLUMNAS_FIJAS:
        if col_name not in df.columns:
            df = df.withColumn(col_name, lit(None))
    return df.select(COLUMNAS_FIJAS)


def cargar_y_analizar_ventas():
    """
    Carga ventas desde MySQL, procesa en Spark,
    y devuelve DataFrame Pandas y resumen
    """
    try:
        spark = get_spark()
        if spark is None:
            raise Exception("No se pudo inicializar Spark")

        cursor = db.get_cursor()
        if cursor is None:
            raise Exception("No hay conexión a MySQL")

        # Consultar ventas
        cursor.execute("SELECT id, cliente, tipo, cantidad, total, fecha FROM ventas")
        ventas_sql = cursor.fetchall()

        if not ventas_sql:
            return pd.DataFrame(), []

        registros = []
        for item in ventas_sql:
            fecha_val = item.get("fecha")
            if isinstance(fecha_val, datetime):
                fecha_val = fecha_val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_val = str(fecha_val) if fecha_val else None

            registros.append({
                "id": str(item.get("id")),
                "cliente": item.get("cliente"),
                "tipo": item.get("tipo"),
                "cantidad": item.get("cantidad"),
                "total": float(item.get("total") or 0),
                "fecha": fecha_val,
            })

        # Crear DataFrame Spark
        df = spark.createDataFrame(registros, schema=schema)

        # Eliminar duplicados
        df = df.dropDuplicates(["id"])

        # Resumen por tipo
        resumen_df = df.groupBy("tipo").agg(
            sum("cantidad").alias("cantidad_total"),
            sum("total").alias("total_ventas")
        )

        # Spark → Pandas
        pd_df = df.toPandas()

        # Convertir fecha
        if "fecha" in pd_df.columns:
            pd_df["fecha"] = pd.to_datetime(pd_df["fecha"], errors="coerce")

        resumen_list = [row.asDict() for row in resumen_df.collect()]

        return pd_df, resumen_list

    except Exception as e:
        print(f"ERROR en cargar_y_analizar_ventas: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), []


def guardar_venta(venta: dict):
    """
    Guarda una venta en MySQL
    """
    try:
        if not isinstance(venta, dict):
            raise ValueError("La venta debe ser un diccionario")

        query = """
            INSERT INTO ventas (cliente, tipo, cantidad, total, fecha)
            VALUES (%s, %s, %s, %s, %s)
        """

        valores = (
            venta.get("cliente"),
            venta.get("tipo"),
            venta.get("cantidad"),
            venta.get("total"),
            venta.get("fecha") or datetime.now()
        )

        cursor.execute(query, valores)
        conn.commit()

    except Exception as e:
        raise Exception(f"Error al guardar venta en MySQL: {e}")