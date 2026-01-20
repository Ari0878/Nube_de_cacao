# services/auth_service.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client["cafeteria_db"]
usuarios_col = db["usuarios"]

def verificar_usuario(correo, password):
    usuario = usuarios_col.find_one({"correo": correo})

    if not usuario:
        return False

    # Verificar usando el hash
    try:
        return check_password_hash(usuario["password"], password)
    except:
        # Fallback por si acaso hay contraseñas en texto plano (no debería pasar)
        return usuario["password"] == password


def registrar_usuario(correo, password):
    # Validación básica
    if not correo or '@' not in correo or '.' not in correo:
        return False, "Ingresa un correo electrónico válido."
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    
    usuario = usuarios_col.find_one({"correo": correo})
    
    if usuario:
        return False, "El correo ya está registrado."

    usuarios_col.insert_one({
        "correo": correo,
        "password": generate_password_hash(password),
        "nombre": correo.split('@')[0].capitalize(),
        "telefono": "",
        "avatar": None
    })

    return True, "Cuenta creada exitosamente."
