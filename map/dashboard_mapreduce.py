import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, count
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Dashboard MapReduce Café", layout="wide")
st.title("Dashboard MapReduce - Análisis de Ventas de Café")

@st.cache_resource
def load_data():
    spark, df, _ = get_spark_session()
    df = df.filter(df["tipo"].isNotNull())
    return spark, df

spark, df = load_data()

st.sidebar.header("Filtros")

tipos = [row["tipo"] for row in df.select("tipo").distinct().collect()]

tipo_seleccionado = st.sidebar.multiselect(
    "Selecciona tipo de café",
    tipos,
    default=tipos
)

df_filtrado = df.filter(df["tipo"].isin(tipo_seleccionado))

st.header("Análisis Agregado (MapReduce)")

resumen = df_filtrado.groupBy("tipo").agg(
    sum("total").alias("total_ventas"),
    sum("cantidad").alias("cantidad_total"),
    count("*").alias("numero_ventas")
)

resumen_pd = resumen.toPandas()

st.dataframe(resumen_pd)

st.subheader("Total de Ventas por Tipo de Café")

fig = plt.figure()

plt.bar(
    resumen_pd["tipo"],
    resumen_pd["total_ventas"]
)

plt.xticks(rotation=45)
plt.xlabel("Tipo de Café")
plt.ylabel("Total de Ventas")
plt.title("Total de Ventas por Tipo de Café")

st.pyplot(fig)

st.subheader("Cantidad de Ventas por Tipo de Café")

fig2 = plt.figure()

plt.bar(
    resumen_pd["tipo"],
    resumen_pd["cantidad_total"]
)

plt.xticks(rotation=45)
plt.xlabel("Tipo de Café")
plt.ylabel("Cantidad Vendida")
plt.title("Cantidad de Ventas por Tipo de Café")

st.pyplot(fig2)

st.subheader("Interpretación Automática")

if not resumen_pd.empty:

    max_ingreso = resumen_pd["total_ventas"].max()
    max_cantidad = resumen_pd["cantidad_total"].max()

    for _, row in resumen_pd.iterrows():

        if row["total_ventas"] == max_ingreso:
            st.success(f"{row['tipo']} → Café más vendido (Mayor ingreso)")

        elif row["cantidad_total"] == max_cantidad:
            st.info(f"{row['tipo']} → Alta rotación")

        else:
            st.warning(f"{row['tipo']} → Venta media")

else:
    st.warning("No hay datos para mostrar.")

st.write("Análisis distribuido usando Apache Spark (MapReduce)")