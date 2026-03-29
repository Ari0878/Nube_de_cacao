# services/auth_service.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timedelta
import random
import string

from db import db

usuarios_col = db["MONGO_COLLECTIONS"]
codigos_recuperacion_col = db["codigos_recuperacion"]


def verificar_usuario(correo, password):
    """Verifica credenciales y retorna el objeto usuario o None"""
    usuario = usuarios_col.find_one({"correo": correo})

    if not usuario:
        return None

    try:
        if check_password_hash(usuario["password"], password):
            usuario_dict = dict(usuario)
            usuario_dict["_id"] = str(usuario_dict["_id"])
            return usuario_dict
        else:
            return None
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return None


def registrar_usuario(correo, password):
    """Registra un nuevo usuario con rol por defecto"""
    if not correo or '@' not in correo or '.' not in correo:
        return False, "Ingresa un correo electrónico válido."
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    
    usuario = usuarios_col.find_one({"correo": correo})
    
    if usuario:
        return False, "El correo ya está registrado."

    nuevo_usuario = {
        "correo": correo,
        "password": generate_password_hash(password),
        "nombre": correo.split('@')[0].capitalize(),
        "telefono": "",
        "avatar": None,
        "roll": "usuario",
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


# ========== FUNCIONES DE RECUPERACIÓN DE CONTRASEÑA ==========

def generar_codigo_recuperacion():
    """Genera un código de 6 dígitos aleatorio"""
    return ''.join(random.choices(string.digits, k=6))


def crear_codigo_recuperacion(correo):
    """
    Crea un código de recuperación para el usuario
    Retorna: (success: bool, codigo: str, mensaje: str)
    """
    # Verificar que el usuario existe
    usuario = usuarios_col.find_one({"correo": correo})
    if not usuario:
        return False, None, "No existe una cuenta con este correo electrónico."
    
    # Generar código
    codigo = generar_codigo_recuperacion()
    
    # Eliminar códigos anteriores del mismo usuario
    codigos_recuperacion_col.delete_many({"correo": correo})
    
    # Guardar código con expiración de 5 minutos
    codigo_data = {
        "correo": correo,
        "codigo": codigo,
        "fecha_creacion": datetime.utcnow(),
        "expiracion": datetime.utcnow() + timedelta(minutes=5),
        "usado": False,
        "intentos": 0
    }
    
    codigos_recuperacion_col.insert_one(codigo_data)
    
    return True, codigo, "Código generado exitosamente."


def verificar_codigo_recuperacion(correo, codigo):
    """
    Verifica si el código es válido
    Retorna: (success: bool, mensaje: str)
    """
    # Buscar código
    codigo_data = codigos_recuperacion_col.find_one({
        "correo": correo,
        "codigo": codigo,
        "usado": False
    })
    
    if not codigo_data:
        return False, "Código inválido o ya fue utilizado."
    
    # Verificar expiración
    if datetime.utcnow() > codigo_data["expiracion"]:
        codigos_recuperacion_col.delete_one({"_id": codigo_data["_id"]})
        return False, "El código ha expirado. Solicita uno nuevo."
    
    # Verificar intentos (máximo 3)
    if codigo_data.get("intentos", 0) >= 3:
        codigos_recuperacion_col.delete_one({"_id": codigo_data["_id"]})
        return False, "Demasiados intentos fallidos. Solicita un nuevo código."
    
    return True, "Código verificado correctamente."


def restablecer_password(correo, codigo, nueva_password):
    """
    Restablece la contraseña del usuario
    Retorna: (success: bool, mensaje: str)
    """
    # Verificar código
    valido, mensaje = verificar_codigo_recuperacion(correo, codigo)
    if not valido:
        # Incrementar intentos fallidos
        codigos_recuperacion_col.update_one(
            {"correo": correo, "codigo": codigo},
            {"$inc": {"intentos": 1}}
        )
        return False, mensaje
    
    # Validar nueva contraseña
    if len(nueva_password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    
    # Actualizar contraseña
    try:
        resultado = usuarios_col.update_one(
            {"correo": correo},
            {"$set": {"password": generate_password_hash(nueva_password)}}
        )
        
        if resultado.modified_count > 0:
            # Marcar código como usado
            codigos_recuperacion_col.update_one(
                {"correo": correo, "codigo": codigo},
                {"$set": {"usado": True}}
            )
            
            return True, "Contraseña restablecida exitosamente."
        else:
            return False, "Error al actualizar la contraseña."
    
    except Exception as e:
        print(f"Error al restablecer contraseña: {e}")
        return False, "Error al procesar la solicitud."


def limpiar_codigos_expirados():
    """Elimina códigos de recuperación expirados (tarea de limpieza)"""
    try:
        resultado = codigos_recuperacion_col.delete_many({
            "expiracion": {"$lt": datetime.utcnow()}
        })
        print(f"Códigos expirados eliminados: {resultado.deleted_count}")
    except Exception as e:
        print(f"Error al limpiar códigos: {e}")