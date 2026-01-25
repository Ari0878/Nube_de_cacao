# services/auth_service.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
<<<<<<< HEAD
from bson import ObjectId
=======
>>>>>>> 780471aaad8e0660f171008fca575cfa4318cd41

client = MongoClient("mongodb://localhost:27017/")
db = client["cafeteria_db"]
usuarios_col = db["usuarios"]

def verificar_usuario(correo, password):
<<<<<<< HEAD
    """Verifica credenciales y retorna el objeto usuario o None"""
    usuario = usuarios_col.find_one({"correo": correo})

    if not usuario:
        return None  # Usuario no encontrado

    # Verificar contraseña
    try:
        if check_password_hash(usuario["password"], password):
            # Convertir ObjectId a string y retornar el objeto completo
            usuario_dict = dict(usuario)
            usuario_dict["_id"] = str(usuario_dict["_id"])
            return usuario_dict
        else:
            return None  # Contraseña incorrecta
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return None


def registrar_usuario(correo, password):
    """Registra un nuevo usuario con rol por defecto"""
=======
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
>>>>>>> 780471aaad8e0660f171008fca575cfa4318cd41
    # Validación básica
    if not correo or '@' not in correo or '.' not in correo:
        return False, "Ingresa un correo electrónico válido."
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    
    usuario = usuarios_col.find_one({"correo": correo})
    
    if usuario:
        return False, "El correo ya está registrado."

<<<<<<< HEAD
    from datetime import datetime
    
    # Crear usuario con rol por defecto
    nuevo_usuario = {
=======
    usuarios_col.insert_one({
>>>>>>> 780471aaad8e0660f171008fca575cfa4318cd41
        "correo": correo,
        "password": generate_password_hash(password),
        "nombre": correo.split('@')[0].capitalize(),
        "telefono": "",
<<<<<<< HEAD
        "avatar": None,
        "roll": "usuario",  # Rol por defecto
        "fecha_creacion": datetime.utcnow(),
        "activo": True,
        "preferencias": {
            "tema": "light",
            "idioma": "es"
        }
    }

    result = usuarios_col.insert_one(nuevo_usuario)
    
    return True, "Cuenta creada exitosamente."


def obtener_usuario_por_email(correo):
    """Obtiene un usuario por su correo"""
    usuario = usuarios_col.find_one({"correo": correo})
    if usuario:
        usuario["_id"] = str(usuario["_id"])
    return usuario
=======
        "avatar": None
    })

    return True, "Cuenta creada exitosamente."
>>>>>>> 780471aaad8e0660f171008fca575cfa4318cd41
