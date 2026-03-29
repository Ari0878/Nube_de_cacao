    from config.mongo_spark_conexion import get_spark_session
    from pyspark.sql.functions import sum 

    spark, df, _ = get_spark_session()

    print("=== MAPREDUCE ===")

    df.printSchema()

    df.groupBy("tipo") \
        .agg(sum("total").alias("total_ventas")) \
        .orderBy("total_ventas", ascending=False) \
        .show()

    spark.stop()
