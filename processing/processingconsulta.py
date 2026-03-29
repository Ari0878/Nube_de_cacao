from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

# ==============================
# CARGAR VARIABLES DEL .ENV
# ==============================

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASSWORD")
cluster = os.getenv("MONGO_CLUSTER")
database_name = os.getenv("MONGO_DB")
collection_name = os.getenv("MONGO_COLLECTIONS")

if not all([user, password, cluster, database_name, collection_name]):
    raise ValueError("Faltan variables en el .env")

# ==============================
# CONEXIÓN A MONGODB
# ==============================

mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)

db = client[database_name]
collection = db[collection_name]

print("Conectado correctamente a MongoDB Atlas\n")

# ==============================
# PIPELINE DE AGREGACIÓN
# ==============================

pipelines = [
    {
        "$addFields": {
            "cantidad_num": {
                "$convert": {
                    "input": "$cantidad",
                    "to": "double",
                    "onError": 0,
                    "onNull": 0
                }
            },
            "total_num": {
                "$convert": {
                    "input": "$total",
                    "to": "double",
                    "onError": 0,
                    "onNull": 0
                }
            }
        }
    },
    {
        "$group": {
            "_id": "$tipo",
            "total_unidades_vendidas": {
                "$sum": "$cantidad_num"
            },
            "ingresos_totales": {
                "$sum": {
                    "$multiply": ["$cantidad_num", "$total_num"]
                }
            },
            "total_ventas": {
                "$sum": 1
            }
        }
    },
    {
        "$sort": {"_id": 1}
    }
]

# ==============================
# EJECUTAR AGREGACIÓN
# ==============================

docs = list(collection.aggregate(pipelines))

# ==============================
# MOSTRAR RESULTADOS
# ==============================

if docs:
    df = pd.DataFrame(docs)
    df.rename(columns={"_id": "tipo"}, inplace=True)

    print("Resultados del procesamiento:\n")
    print(df.to_string(index=False))
else:
    print("No hay documentos en la colección.")