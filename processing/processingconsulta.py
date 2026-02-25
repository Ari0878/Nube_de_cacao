from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

# Cargar .env correctamente
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASSWORD")
cluster = os.getenv("MONGO_CLUSTER")
database_name = os.getenv("MONGO_DB")
collection_name = os.getenv("MONGO_COLLECTIONS")

print("DB:", database_name)
print("COLLECTION:", collection_name)

if not all([user, password, cluster, database_name, collection_name]):
    raise ValueError("Faltan variables en el .env")

mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)

db = client[database_name]
collection = db[collection_name]

print("\n Conectado correctamente\n")

# Mostrar datos tipo tabla
docs = list(collection.find({}, {"_id": 0}))

if docs:
    df = pd.DataFrame(docs)
    print(" Datos de la colección:\n")
    print(df.to_string(index=False))
else:
    print(" No hay documentos en la colección.")