# db.py
# ---------------------- CONEXIÓN A MONGODB ATLAS ----------------------

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    # Obtener variables del .env
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
    MONGO_DB = os.getenv("MONGO_DB")

    # Construir URI de conexión
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority"

    # Crear cliente
    client = MongoClient(uri)

    # Base de datos
    db = client[MONGO_DB]

    # Colecciones
    productos_col = db["productos"]
    ventas_col = db["ventas"]
    usuarios_col = db["usuarios"]

    # Probar conexión
    client.server_info()
    print("✅ Conectado correctamente a MongoDB Atlas")

except Exception as e:
    print(f"❌ CRITICAL: No se pudo conectar a MongoDB Atlas: {e}")

    client = None
    db = None
    productos_col = None
    ventas_col = None
    usuarios_col = None