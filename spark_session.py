# spark_session.py

import streamlit as st
from pyspark.sql import SparkSession

@st.cache_resource
def get_spark():
    """
    Crea y devuelve una instancia de SparkSession, cacheada por Streamlit.
    """
    try:
        print("INFO: Creando nueva sesión de Spark...")
        spark = SparkSession.builder \
            .appName("CafeteriaPySparkStreamlit") \
            .getOrCreate()

        # --- LÍNEA DE CORRECCIÓN DEFINITIVA ---
        # Deshabilitamos la optimización de Arrow para evitar el error de datetime.
        # Esto fuerza a Spark a usar un método de conversión más seguro.
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

        return spark
    except Exception as e:
        st.error(f"Error crítico de PySpark: No se pudo iniciar la sesión de Spark: {e}")
        return None

def stop_spark():
    """Detiene la sesión Spark si está activa."""
    try:
        spark = get_spark()
        if spark is not None:
            print("INFO: Deteniendo sesión de Spark...")
            spark.stop()
        st.cache_resource.clear()
    except Exception as e:
        st.warning(f"No se pudo detener Spark limpiamente: {e}")