from pyspark.sql import SparkSession
from dotenv import load_dotenv
import os

def get_spark_session():
    load_dotenv()

    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASSWORD")
    cluster = os.getenv("MONGO_CLUSTER")
    database = os.getenv("MONGO_DB")
    collection = os.getenv("MONGO_COLLECTIONS")

    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}/{database}?retryWrites=true&w=majority"

    spark = SparkSession.builder \
    .appName("Nube_de_cacao") \
    .config("spark.jars.packages",
    "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
    .config("spark.mongodb.read.connection.uri", mongo_uri) \
    .config("spark.mongodb.read.database", database) \
    .config("spark.mongodb.read.collection", collection) \
    .getOrCreate()

    df = spark.read.format("mongodb").load()

    return spark, df, mongo_uri
