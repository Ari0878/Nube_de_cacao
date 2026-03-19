# services/auth_service.py
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
from db import cursor, conn


# Roles disponibles
DEFAULT_ROLE = "usuario"
ADMIN_ROLE = "admin"
VALID_ROLES = {DEFAULT_ROLE, ADMIN_ROLE}


def es_rol_valido(rol):
    """Valida si un rol es válido."""
    return rol in VALID_ROLES


def obtener_rol_inicial():
    """Devuelve el rol inicial para el primer usuario.

    Si aún no existen administradores, el primer usuario será administrador.
    """
    try:
        if cursor is None:
            return DEFAULT_ROLE
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = %s", (ADMIN_ROLE,))
        row = cursor.fetchone()
        if row:
            total = row.get("total") or row.get("COUNT(*)") or 0
            if int(total) == 0:
                return ADMIN_ROLE
    except Exception:
        pass
    return DEFAULT_ROLE


def verificar_usuario(correo, password):
    """Verifica credenciales y retorna el objeto usuario o None"""
    try:
        if cursor is None:
            print("Error: No hay conexión a la base de datos")
            return None
        
        # Buscar por correo (así se llama la columna en tu BD)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return None
        
        # Verificar contraseña
        try:
            if check_password_hash(usuario["password"], password):
                usuario_dict = dict(usuario)
                # Convertir fechas a string para JSON
                for key, value in usuario_dict.items():
                    if isinstance(value, datetime):
                        usuario_dict[key] = value.isoformat()
                return usuario_dict
            else:
                return None
        except Exception as e:
            print(f"Error verificando contraseña: {e}")
            return None
            
    except Exception as e:
        print(f"Error en verificar_usuario: {e}")
        return None


def registrar_usuario(correo, password):
    """Registra un nuevo usuario con rol por defecto"""
    try:
        if cursor is None or conn is None:
            return False, "Error de conexión a la base de datos"
        
        if not correo or '@' not in correo or '.' not in correo:
            return False, "Ingresa un correo electrónico válido."
        
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            return False, "El correo ya está registrado."
        
        # Insertar nuevo usuario con TODAS las columnas de tu tabla
        nombre = correo.split('@')[0].capitalize()
        password_hash = generate_password_hash(password)
        ahora = datetime.now()
        rol = obtener_rol_inicial()
        
        query = """
            INSERT INTO usuarios (
                nombre, correo, password, telefono, avatar, rol, activo,
                fecha_creacion, fecha_actualizacion, fecha_cambio_password,
                tema_preferido, idioma, fecha_pref
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        valores = (
            nombre,                    # nombre
            correo,                    # correo
            password_hash,             # password
            None,                      # telefono (NULL)
            "default.png",           # avatar
            rol,                       # rol
            1,                         # activo (TRUE)
            ahora,                     # fecha_creacion
            None,                      # fecha_actualizacion (NULL)
            None,                      # fecha_cambio_password (NULL)
            "auto",                  # tema_preferido
            "es",                    # idioma
            None                      # fecha_pref (NULL)
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        return True, "Cuenta creada exitosamente."
        
    except Exception as e:
        print(f"Error en registrar_usuario: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error al registrar: {str(e)}"


def obtener_usuario_por_correo(correo):
    """Obtiene un usuario por su correo"""
    try:
        if cursor is None:
            return None
        
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if usuario:
            usuario_dict = dict(usuario)
            for key, value in usuario_dict.items():
                if isinstance(value, datetime):
                    usuario_dict[key] = value.isoformat()
            return usuario_dict
        return None
        
    except Exception as e:
        print(f"Error en obtener_usuario_por_correo: {e}")
        return None


def listar_usuarios():
    """Obtiene una lista de todos los usuarios (para administración)"""
    try:
        if cursor is None:
            return []

        cursor.execute("SELECT id, nombre, correo, rol, activo, fecha_creacion FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall() or []

        for u in usuarios:
            if isinstance(u.get("fecha_creacion"), datetime):
                u["fecha_creacion"] = u["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S")
        return usuarios
    except Exception as e:
        print(f"Error en listar_usuarios: {e}")
        return []


def cambiar_rol_usuario(correo, nuevo_rol):
    """Cambia el rol de un usuario"""
    if not es_rol_valido(nuevo_rol):
        return False, "Rol inválido"

    try:
        if cursor is None or conn is None:
            return False, "Error de conexión a la base de datos"

        cursor.execute("UPDATE usuarios SET rol = %s WHERE correo = %s", (nuevo_rol, correo))
        conn.commit()
        return True, "Rol actualizado correctamente"
    except Exception as e:
        print(f"Error en cambiar_rol_usuario: {e}")
        return False, f"Error al cambiar rol: {str(e)}"


# ========== FUNCIONES DE RECUPERACIÓN DE CONTRASEÑA ==========

def generar_codigo_recuperacion():
    """Genera un código de 6 dígitos aleatorio"""
    return ''.join(random.choices(string.digits, k=6))


def crear_codigo_recuperacion(correo):
    """
    Crea un código de recuperación para el usuario
    """
    try:
        if cursor is None or conn is None:
            return False, None, "Error de conexión a la base de datos"
        
        # Verificar que el usuario existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return False, None, "No existe una cuenta con este correo electrónico."
        
        # Crear tabla de códigos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS codigos_recuperacion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                correo VARCHAR(150),
                codigo VARCHAR(10),
                fecha_creacion DATETIME,
                expiracion DATETIME,
                usado BOOLEAN DEFAULT FALSE,
                intentos INT DEFAULT 0,
                INDEX idx_correo (correo),
                INDEX idx_codigo (codigo)
            )
        """)
        conn.commit()
        
        # Generar código
        codigo = generar_codigo_recuperacion()
        
        # Eliminar códigos anteriores
        cursor.execute("DELETE FROM codigos_recuperacion WHERE correo = %s", (correo,))
        
        # Guardar nuevo código
        fecha_creacion = datetime.now()
        expiracion = fecha_creacion + timedelta(minutes=5)
        
        cursor.execute("""
            INSERT INTO codigos_recuperacion 
            (correo, codigo, fecha_creacion, expiracion, usado, intentos)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (correo, codigo, fecha_creacion, expiracion, False, 0))
        
        conn.commit()
        
        return True, codigo, "Código generado exitosamente."
        
    except Exception as e:
        print(f"Error en crear_codigo_recuperacion: {e}")
        return False, None, f"Error al generar código: {str(e)}"


def verificar_codigo_recuperacion(correo, codigo):
    """Verifica si el código es válido"""
    try:
        if cursor is None:
            return False, "Error de conexión a la base de datos"
        
        cursor.execute("""
            SELECT * FROM codigos_recuperacion 
            WHERE correo = %s AND codigo = %s AND usado = FALSE
        """, (correo, codigo))
        
        codigo_data = cursor.fetchone()
        
        if not codigo_data:
            return False, "Código inválido o ya fue utilizado."
        
        if datetime.now() > codigo_data["expiracion"]:
            cursor.execute("DELETE FROM codigos_recuperacion WHERE id = %s", (codigo_data["id"],))
            conn.commit()
            return False, "El código ha expirado. Solicita uno nuevo."
        
        if codigo_data.get("intentos", 0) >= 3:
            cursor.execute("DELETE FROM codigos_recuperacion WHERE id = %s", (codigo_data["id"],))
            conn.commit()
            return False, "Demasiados intentos fallidos. Solicita un nuevo código."
        
        return True, "Código verificado correctamente."
        
    except Exception as e:
        print(f"Error en verificar_codigo_recuperacion: {e}")
        return False, f"Error al verificar código: {str(e)}"


def restablecer_password(correo, codigo, nueva_password):
    """Restablece la contraseña del usuario"""
    try:
        if cursor is None or conn is None:
            return False, "Error de conexión a la base de datos"
        
        valido, mensaje = verificar_codigo_recuperacion(correo, codigo)
        if not valido:
            cursor.execute("""
                UPDATE codigos_recuperacion 
                SET intentos = intentos + 1 
                WHERE correo = %s AND codigo = %s
            """, (correo, codigo))
            conn.commit()
            return False, mensaje
        
        if len(nueva_password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."
        
        nueva_hash = generate_password_hash(nueva_password)
        ahora = datetime.now()
        
        cursor.execute("""
            UPDATE usuarios 
            SET password = %s, fecha_cambio_password = %s
            WHERE correo = %s
        """, (nueva_hash, ahora, correo))
        
        if cursor.rowcount > 0:
            cursor.execute("""
                UPDATE codigos_recuperacion 
                SET usado = TRUE 
                WHERE correo = %s AND codigo = %s
            """, (correo, codigo))
            conn.commit()
            return True, "Contraseña restablecida exitosamente."
        else:
            return False, "Error al actualizar la contraseña."
        
    except Exception as e:
        print(f"Error en restablecer_password: {e}")
        return False, f"Error al procesar la solicitud: {str(e)}"


def limpiar_codigos_expirados():
    """Elimina códigos de recuperación expirados"""
    try:
        if cursor is None or conn is None:
            return
        
        cursor.execute("DELETE FROM codigos_recuperacion WHERE expiracion < %s", (datetime.now(),))
        conn.commit()
        print(f"Códigos expirados eliminados: {cursor.rowcount}")
        
    except Exception as e:
        print(f"Error al limpiar códigos: {e}")