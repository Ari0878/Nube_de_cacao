# services/perfil_service.py
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from db import cursor, conn

UPLOAD_FOLDER = "static/uploads/avatars"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Crear carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def obtener_datos_usuario(correo):
    """Obtiene los datos del usuario para mostrar en el perfil"""
    try:
        if cursor is None:
            print("Error: No hay conexión a la base de datos")
            return None
        
        cursor.execute("""
            SELECT id, nombre, correo, telefono, avatar, fecha_creacion, 
                   tema_preferido, idioma, rol
            FROM usuarios 
            WHERE correo = %s
        """, (correo,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            return None
        
        # Formatear fecha
        fecha_reg = usuario.get("fecha_creacion")
        if isinstance(fecha_reg, datetime):
            fecha_reg = fecha_reg.strftime("%d/%m/%Y")
        else:
            fecha_reg = "N/A"
        
        return {
            "id": usuario.get("id"),
            "nombre": usuario.get("nombre", "Usuario"),
            "correo": usuario.get("correo", ""),
            "telefono": usuario.get("telefono", ""),
            "avatar": usuario.get("avatar", "default.png"),
            "fecha_registro": fecha_reg,
            "tema_preferido": usuario.get("tema_preferido", "auto"),
            "idioma": usuario.get("idioma", "es"),
            "rol": usuario.get("rol", "usuario")
        }
    except Exception as e:
        print(f"Error en obtener_datos_usuario: {e}")
        return None


def actualizar_datos_usuario(correo, nombre, nuevo_correo, telefono=None):
    """Actualiza la información personal del usuario"""
    try:
        if cursor is None or conn is None:
            return False, "No hay conexión a la base de datos"
        
        ahora = datetime.now()
        
        # Si el correo cambió, verificar que no exista
        if correo != nuevo_correo:
            cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (nuevo_correo,))
            existe = cursor.fetchone()
            if existe:
                return False, "El nuevo correo ya está registrado."
            
            cursor.execute("""
                UPDATE usuarios 
                SET nombre = %s, correo = %s, telefono = %s, 
                    fecha_actualizacion = %s
                WHERE correo = %s
            """, (nombre, nuevo_correo, telefono, ahora, correo))
        else:
            cursor.execute("""
                UPDATE usuarios 
                SET nombre = %s, telefono = %s, fecha_actualizacion = %s
                WHERE correo = %s
            """, (nombre, telefono, ahora, correo))
        
        conn.commit()
        return True, "Datos actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"


def cambiar_password_usuario(correo, password_actual, password_nueva):
    """Cambia la contraseña del usuario"""
    try:
        if cursor is None or conn is None:
            return False, "No hay conexión a la base de datos"
        
        # Obtener usuario
        cursor.execute("SELECT password FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return False, "Usuario no encontrado."
        
        # Verificar contraseña actual
        if not check_password_hash(usuario["password"], password_actual):
            return False, "La contraseña actual es incorrecta."
        
        # Validar nueva contraseña
        if len(password_nueva) < 6:
            return False, "La nueva contraseña debe tener al menos 6 caracteres."
        
        # Actualizar contraseña
        nueva_hash = generate_password_hash(password_nueva)
        ahora = datetime.now()
        
        cursor.execute("""
            UPDATE usuarios 
            SET password = %s, fecha_cambio_password = %s
            WHERE correo = %s
        """, (nueva_hash, ahora, correo))
        
        conn.commit()
        return True, "Contraseña cambiada correctamente."
        
    except Exception as e:
        print(f"Error en cambiar_password_usuario: {e}")
        return False, f"Error al cambiar contraseña: {str(e)}"


def guardar_avatar(correo, file):
    """Guarda la foto de perfil del usuario"""
    try:
        if not file or file.filename == '':
            return False, "No se seleccionó ningún archivo."
        
        if not allowed_file(file.filename):
            return False, "Tipo de archivo no permitido. Use PNG, JPG o GIF."
        
        # Crear nombre seguro
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{correo.replace('@', '_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
        filename = secure_filename(filename)
        
        # Guardar archivo
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Actualizar en base de datos
        if cursor is not None and conn is not None:
            cursor.execute("""
                UPDATE usuarios 
                SET avatar = %s, fecha_avatar = %s
                WHERE correo = %s
            """, (filename, datetime.now(), correo))
            conn.commit()
        
        return True, "Foto de perfil actualizada."
    except Exception as e:
        return False, f"Error al guardar foto: {str(e)}"


def guardar_preferencias(correo, tema, idioma):
    """Guarda las preferencias del usuario"""
    try:
        if cursor is None or conn is None:
            return False, "No hay conexión a la base de datos"
        
        cursor.execute("""
            UPDATE usuarios 
            SET tema_preferido = %s, idioma = %s, fecha_pref = %s
            WHERE correo = %s
        """, (tema, idioma, datetime.now(), correo))
        
        conn.commit()
        return True, "Preferencias guardadas."
    except Exception as e:
        return False, f"Error al guardar preferencias: {str(e)}"


def eliminar_cuenta(correo, password):
    """Elimina la cuenta del usuario (requiere confirmación de contraseña)"""
    try:
        if cursor is None or conn is None:
            return False, "No hay conexión a la base de datos"
        
        # Verificar contraseña
        cursor.execute("SELECT password FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return False, "Usuario no encontrado."
        
        if not check_password_hash(usuario["password"], password):
            return False, "Contraseña incorrecta."
        
        # Eliminar cuenta (o desactivar)
        cursor.execute("DELETE FROM usuarios WHERE correo = %s", (correo,))
        conn.commit()
        
        return True, "Cuenta eliminada correctamente."
        
    except Exception as e:
        return False, f"Error al eliminar cuenta: {str(e)}"