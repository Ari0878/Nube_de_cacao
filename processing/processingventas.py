from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASSWORD")
cluster = os.getenv("MONGO_CLUSTER")
database_name = os.getenv("MONGO_DB")
collection_name = os.getenv("MONGO_COLLECTIONS")

if not all([user, password, cluster, database_name, collection_name]):
    raise ValueError("Faltan variables en el .env")


# CONEXIÓN A MONGODB
mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)

db = client[database_name]
collection = db[collection_name]


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
        "$addFields": {
            "ingreso": {
                "$multiply": ["$cantidad_num", "$total_num"]
            }
        }
    },

    {
        "$group": {
            "_id": "$tipo",

            "total_ventas": { "$sum": 1 },

            "ingresos_totales": {
                "$sum": "$ingreso"
            },

            "promedio_por_venta": {
                "$avg": "$ingreso"
            },

            "venta_maxima": {
                "$max": "$ingreso"
            },

            "venta_minima": {
                "$min": "$ingreso"
            }
        }
    },


    {
        "$sort": { "ingresos_totales": -1 }
    }
]



docs = list(collection.aggregate(pipelines))

if docs:
    df = pd.DataFrame(docs)
    df.rename(columns={"_id": "tipo"}, inplace=True)

    print(df.to_string(index=False))
else:
    print("No hay documentos en la colección.")