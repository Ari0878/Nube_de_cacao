# services/perfil_service.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from db import db

usuarios_col = db["usuarios"]

UPLOAD_FOLDER = "static/uploads/avatars"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def actualizar_datos_usuario(correo, nombre, nuevo_correo, telefono=None):
    """Actualiza la información personal del usuario."""
    try:
        update_data = {
            "nombre": nombre,
            "telefono": telefono,
            "fecha_actualizacion": datetime.now()
        }
        
        # Si el correo cambió, verificar que no exista
        if correo != nuevo_correo:
            existe = usuarios_col.find_one({"correo": nuevo_correo})
            if existe:
                return False, "El nuevo correo ya está registrado."
            update_data["correo"] = nuevo_correo
        
        usuarios_col.update_one(
            {"correo": correo},
            {"$set": update_data}
        )
        
        return True, "Datos actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"


def cambiar_password_usuario(correo, password_actual, password_nueva):
    """Cambia la contraseña del usuario."""
    try:
        usuario = usuarios_col.find_one({"correo": correo})
        
        if not usuario:
            return False, "Usuario no encontrado."
        
        # Verificar contraseña actual usando la misma lógica que el login
        try:
            if not check_password_hash(usuario["password"], password_actual):
                return False, "La contraseña actual es incorrecta."
        except:
            # Fallback para contraseñas en texto plano
            if usuario["password"] != password_actual:
                return False, "La contraseña actual es incorrecta."
        
        # Actualizar con nueva contraseña
        usuarios_col.update_one(
            {"correo": correo},
            {"$set": {
                "password": generate_password_hash(password_nueva),
                "fecha_cambio_password": datetime.now()
            }}
        )
        
        return True, "Contraseña cambiada correctamente."
    except Exception as e:
        print(f"Error cambiar_password_usuario: {e}")
        return False, f"Error al cambiar contraseña: {str(e)}"


def guardar_avatar(correo, file):
    """Guarda la foto de perfil del usuario."""
    try:
        if not file or file.filename == '':
            return False, "No se seleccionó ningún archivo."
        
        if not allowed_file(file.filename):
            return False, "Tipo de archivo no permitido. Use PNG, JPG o GIF."
        
        # Crear nombre seguro con el correo del usuario
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{correo.replace('@', '_').replace('.', '_')}.{extension}"
        filename = secure_filename(filename)
        
        # Asegurar que la carpeta existe
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Guardar archivo
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Actualizar en base de datos
        usuarios_col.update_one(
            {"correo": correo},
            {"$set": {
                "avatar": filename,
                "fecha_avatar": datetime.now()
            }}
        )
        
        return True, "Foto de perfil actualizada."
    except Exception as e:
        return False, f"Error al guardar foto: {str(e)}"


def obtener_datos_usuario(correo):
    """Obtiene los datos del usuario para mostrar en el perfil."""
    usuario = usuarios_col.find_one({"correo": correo})
    
    if not usuario:
        return None
    
    avatar_value = usuario.get("avatar", "default.png")
    if isinstance(avatar_value, (bytes, bytearray)):
        # Si el avatar está guardado como bytes, lo reemplazamos por la imagen por defecto
        avatar_value = "default.png"
        # Actualizamos la base de datos para corregir el valor
        usuarios_col.update_one({"correo": correo}, {"$set": {"avatar": avatar_value}})
    return {
        "nombre": usuario.get("nombre", "Usuario"),
        "correo": usuario.get("correo", ""),
        "telefono": usuario.get("telefono", ""),
        "avatar": avatar_value,
        "fecha_registro": usuario.get("_id").generation_time.strftime("%d/%m/%Y") if usuario.get("_id") else "N/A",
        "tema_preferido": usuario.get("tema_preferido", "auto"),
        "idioma": usuario.get("idioma", "es")
    }


def guardar_preferencias(correo, tema, idioma):
    """Guarda las preferencias del usuario."""
    try:
        usuarios_col.update_one(
            {"correo": correo},
            {"$set": {
                "tema_preferido": tema,
                "idioma": idioma,
                "fecha_pref": datetime.now()
            }}
        )
        return True, "Preferencias guardadas."
    except Exception as e:
        return False, f"Error al guardar preferencias: {str(e)}"
