# db.py
# ---------------------- CONEXIÓN A MONGODB ----------------------
from pymongo import MongoClient

try:
    # Conexión local a MongoDB
    client = MongoClient("mongodb://localhost:27017/")

    # Base de datos principal
    db = client["cafeteria_db"]

    # Colecciones
    collection = db["ventas"]
    usuarios_col = db["usuarios"]

    # Probar conexión
    client.server_info()

except Exception as e:
    # No detener el servidor Flask.
    print(f"CRITICAL: No se pudo conectar a MongoDB: {e}")

    # Variables en None para evitar errores en los módulos que importen db
    client = None
    db = None
    collection = None
    usuarios_col = None
