# services/ventas_service.py

from datetime import datetime
import pandas as pd

from db import ventas_col   
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


# --- Esquema Spark ---
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
    try:
        spark = get_spark()
        if spark is None:
            raise Exception("No se pudo inicializar Spark correctamente")


        ventas_mongo = list(
            ventas_col.find({}, {col: 1 for col in COLUMNAS_FIJAS})
        )

        if not ventas_mongo:
            return pd.DataFrame(), []

        registros = []

        for item in ventas_mongo:
            item["_id"] = str(item.get("_id"))

            fecha_obj = item.get("fecha")
            if isinstance(fecha_obj, datetime):
                item["fecha"] = fecha_obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
            else:
                item["fecha"] = str(fecha_obj) if fecha_obj else None

            registros.append(item)

        df = spark.createDataFrame(registros, schema=schema)
        df = df.dropDuplicates(["_id"])

        resumen_df = df.groupBy("tipo").agg(
            sum("cantidad").alias("cantidad_total"),
            sum("total").alias("total_ventas")
        )

        pd_df = df.toPandas()

        if "fecha" in pd_df.columns:
            pd_df["fecha"] = pd.to_datetime(pd_df["fecha"], errors="coerce")

        resumen_list = [row.asDict() for row in resumen_df.collect()]

        return pd_df, resumen_list

    except Exception as e:
        print(f"ERROR en cargar_y_analizar_ventas: {e}")
        return pd.DataFrame(), []


def guardar_venta_mongo(venta: dict):
    try:
        if not isinstance(venta, dict):
            raise ValueError("La venta debe ser un diccionario válido.")


        ventas_col.insert_one(venta)

    except Exception as e:
        raise Exception(f"Error al guardar venta en MongoDB: {e}")