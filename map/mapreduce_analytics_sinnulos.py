from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum
import matplotlib.pyplot as plt
import pandas as pd


def interpretar_mapreduce(resumen_df):

    resumen_pd = resumen_df.toPandas()

    print("\n")
    print("Interpretación automatica mapreduce:")
    print("\n")

    max_ventas = resumen_pd['total_ventas'].max()
    min_ventas = resumen_pd['total_ventas'].min()
    avg_ventas = resumen_pd['total_ventas'].mean()

    for _, row in resumen_pd.iterrows():
        tipo = row['tipo']
        total_ventas = round(row['total_ventas'], 2)
        cantidad = row['cantidad']

        print(f"Tipo de café: {tipo}")
        print(f"  Total de ventas: {total_ventas}")
        print(f"  Cantidad: {cantidad}")
        print()

        if total_ventas == max_ventas:
            print(f"El tipo de café con MAYORES ventas es '{tipo}' con {total_ventas}.\n")
        elif total_ventas == min_ventas:
            print(f"El tipo de café con MENORES ventas es '{tipo}' con {total_ventas}.\n")
        else:
            print(f"El tipo de café '{tipo}' tiene {total_ventas} ventas.\n")


def graficar_resultados(resumen_df):

    pdf = resumen_df.toPandas()

    plt.figure(figsize=(10, 6))
    plt.bar(pdf["tipo"], pdf["total_ventas"], color=["#FF5733", "#33C1FF", "#75FF33"])

    plt.title("Total de Ventas por Tipo de Café")
    plt.xlabel("Tipo de Café")
    plt.ylabel("Total de Ventas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def graficar_cantidad_ventas(resumen_df):

    pdf = resumen_df.toPandas()

    plt.figure(figsize=(10, 6))
    plt.bar(pdf["tipo"], pdf["cantidad"], color=["#FF5733", "#33C1FF", "#75FF33"])

    plt.title("Cantidad de Ventas por Tipo de Café")
    plt.xlabel("Tipo de Café")
    plt.ylabel("Cantidad de Ventas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():

    spark, df, _ = get_spark_session()

    print("=== MAPREDUCE ===")

    # llenar valores nulos
    df = df.fillna({"tipo": "Desconocido"})

    # agregación tipo MapReduce
    resumen = df.groupBy("tipo").agg(
        sum("total").alias("total_ventas"),
        sum("cantidad").alias("cantidad")
    )

    resumen.show()

    interpretar_mapreduce(resumen)

    graficar_resultados(resumen)

    graficar_cantidad_ventas(resumen)

    spark.stop()


if __name__ == "__main__":
    main()