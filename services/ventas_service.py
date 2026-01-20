# services/ventas_service.py

from datetime import datetime
import pandas as pd

from db import collection
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
COLUMNAS_FIJAS = ["_id", "cliente", "tipo", "cantidad", "total", "fecha"]


# --- Esquema Spark (fecha como StringType) ---
schema = StructType([
    StructField("_id", StringType(), True),
    StructField("cliente", StringType(), True),
    StructField("tipo", StringType(), True),
    StructField("cantidad", IntegerType(), True),
    StructField("total", FloatType(), True),
    StructField("fecha", StringType(), True),
])


def normalizar_df(df):
    """Asegura que el DataFrame tenga todas las columnas necesarias y en orden."""
    for col_name in COLUMNAS_FIJAS:
        if col_name not in df.columns:
            df = df.withColumn(col_name, lit(None))
    return df.select(COLUMNAS_FIJAS)


def cargar_y_analizar_ventas():
    """
    Carga ventas desde MongoDB, procesa en Spark, convierte fechas,
    y devuelve:
    - DataFrame Pandas completo
    - Lista resumen para gráficas (ventas totales por tipo)
    """

    try:
        spark = get_spark()
        if spark is None:
            raise Exception("No se pudo inicializar Spark correctamente")

        # Leer datos desde Mongo
        ventas_mongo = list(
            collection.find({}, {col: 1 for col in COLUMNAS_FIJAS})
        )

        if not ventas_mongo:
            return pd.DataFrame(), []

        registros = []

        # Convertir _id y fecha a texto
        for item in ventas_mongo:
            item["_id"] = str(item.get("_id"))

            fecha_obj = item.get("fecha")
            if isinstance(fecha_obj, datetime):
                item["fecha"] = fecha_obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            else:
                item["fecha"] = str(fecha_obj) if fecha_obj else None

            registros.append(item)

        # Crear DataFrame Spark con esquema forzado
        df = spark.createDataFrame(registros, schema=schema)

        # Eliminar duplicados
        df = df.dropDuplicates(["_id"])

        # Resumen (ventas por tipo)
        resumen_df = df.groupBy("tipo").agg(
            sum("cantidad").alias("cantidad_total"),
            sum("total").alias("total_ventas")
        )

        # Convertir Spark → Pandas
        pd_df = df.toPandas()

        # Reconstruir fecha ahora en pandas
        if "fecha" in pd_df.columns:
            pd_df["fecha"] = pd.to_datetime(pd_df["fecha"], errors="coerce")

        # Resumen como lista de diccionarios
        resumen_list = [row.asDict() for row in resumen_df.collect()]

        return pd_df, resumen_list

    except Exception as e:
        print(f"ERROR en cargar_y_analizar_ventas: {e}")
        return pd.DataFrame(), []


def guardar_venta_mongo(venta: dict):
    """
    Guarda una venta en MongoDB.
    En Flask no se usan toasts, solo raise en caso de error.
    """
    try:
        if not isinstance(venta, dict):
            raise ValueError("La venta debe ser un diccionario válido.")

        collection.insert_one(venta)

    except Exception as e:
        raise Exception(f"Error al guardar venta en MongoDB: {e}")
