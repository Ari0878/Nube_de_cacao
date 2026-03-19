from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("TestSpark").getOrCreate()
spark.range(5).show()