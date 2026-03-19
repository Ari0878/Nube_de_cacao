from pymongo import MongoClient

uri = "mongodb+srv://hector1985:Aime131985@utvt.qqqotrr.mongodb.net/?appName=UTVT"
client = MongoClient(uri)

db = client["escuela"]
collection = db["estudiantes"]

documentos = {
    "nombre": "Café Americano",
    "descripcion": "Café  y un toque de leche",
    "precio": 2.50,
    "categoria": "Bebidas",
}

resultado = collection.insert_one(documentos)
print(f"Documento insertado con ID: {resultado.inserted_id}")

for doc in collection.find():
    print(doc)


#Borrar la base de datos
# from pymongo import MongoClient

# uri = "mongodb+srv://hector1985:Aime131985@utvt.qqqotrr.mongodb.net/?appName=UTVT"
# client = MongoClient(uri)

# # Eliminar la base de datos
# client.drop_database("cafeteria_db")

# print("Base de datos eliminada correctamente")