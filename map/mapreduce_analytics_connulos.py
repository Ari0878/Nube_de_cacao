from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, avg, count
from matplotlib import pyplot as plt
import pandas as pd

def interpretar_mapreduce(resumen_df):

    resumen_df = resumen_df.toPandas()

    print("\n")
    print("INTERPRETACIÓN DE RESULTADOS:")
    print("\n")

    max_ingresos = resumen_df["ingresos_totales"].max()
    max_tipo = resumen_df[resumen_df["ingresos_totales"] == max_ingresos]["tipo"].values[0]

    for _, row in resumen_df.iterrows():

        tipo = row["tipo"]
        total_ventas = row["total_ventas"]
        ingresos_totales = row["ingresos_totales"]
        promedio_por_venta = row["promedio_por_venta"]

        tipo = row["tipo"]
        total_ventas = row["total_ventas"]
        ingresos_totales = round(row["ingresos_totales"], 2)
        promedio_por_venta = round(row["promedio_por_venta"], 2)

        print(f"Tipo: {tipo}")
        print(f"  Total de ventas: {total_ventas}")
        print(f"  Ingresos totales: ${ingresos_totales}")
        print(f"  Promedio por venta: ${promedio_por_venta}")
        print("\n")

        if ingresos_totales == max_ingresos:
            print(f"El tipo de café con mayores ingresos es '{tipo}' con ${ingresos_totales} en ventas.\n")
        elif tipo == max_tipo:
            print(f"El tipo de café '{tipo}' tiene ingresos totales de ${ingresos_totales}, que es el máximo registrado.\n")
        else:
            print(f"El tipo de café '{tipo}' tiene ingresos totales de ${ingresos_totales}.\n")
        
        print()

def graficar_resultados(resumen_df):

    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["tipo"], pdf["ingresos_totales"], color=["#FF5733", "#33C1FF", "#75FF33"])

    plt.title("Ingresos Totales por Tipo de Café")
    plt.xlabel("Tipo de Café")
    plt.ylabel("Ingresos Totales ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def graficar_cantidad_ventas(resumen_df):
    
    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["tipo"], pdf["total_ventas"], color=["#FF5733", "#33C1FF", "#75FF33"])

    plt.title("Cantidad de Ventas por Tipo de Café")
    plt.xlabel("Tipo de Café")
    plt.ylabel("Cantidad de Ventas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    
    spark, df, _ = get_spark_session()

    print("=== MAPREDUCE ===")

    df.printSchema()

    resumen_df = df.groupBy("tipo").agg(
        count("*").alias("total_ventas"),
        sum("total").alias("ingresos_totales"),
        avg("total").alias("promedio_por_venta")
    ).orderBy("ingresos_totales", ascending=False)

    resumen_df.show()

    interpretar_mapreduce(resumen_df)
    graficar_resultados(resumen_df)
    graficar_cantidad_ventas(resumen_df)

    spark.stop()

if __name__ == "__main__":
    main()