# services/roles_service.py
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash
from db import db

roles_col = db["MONGO_COLLECTIONS"]
usuarios_col = db["MONGO_COLLECTIONS"]


def crear_rol(nombre, descripcion, correo=None, password=None, permisos=None, estado="activo"):
    """
    Crea un nuevo rol en MONGO_COLLECTIONS
    
    Args:
        nombre (str): Nombre del rol
        descripcion (str): Descripción del rol
        correo (str): Correo electrónico del usuario con este rol
        password (str): Contraseña encriptada del usuario
        permisos (list): Lista de permisos para este rol
        estado (str): Estado del rol (activo/inactivo)
    
    Returns:
        (success: bool, mensaje: str, rol_id: str)
    """
    try:
        if not nombre or not nombre.strip():
            return False, "El nombre del rol es obligatorio", None
        
        # Verificar que no exista un rol con el mismo nombre
        existe = roles_col.find_one({"roll": {"$in": ["admin", "usuario"]}, "nombre": nombre.lower()})
        if existe:
            return False, "Ya existe un rol con este nombre", None
        
        # Validar email si se proporciona
        if correo:
            if '@' not in correo or '.' not in correo:
                return False, "Email inválido", None
            
            # Verificar que el email no esté registrado
            email_existe = usuarios_col.find_one({"correo": correo, "roll": {"$in": ["admin", "usuario"]}})
            if email_existe:
                return False, "El correo ya está registrado", None
            
            if not password or len(password) < 6:
                return False, "La contraseña debe tener al menos 6 caracteres", None
        
        # Permisos por defecto
        if permisos is None:
            permisos = {}
        
        nuevo_rol = {
            "nombre": nombre.strip(),
            "descripcion": descripcion.strip() if descripcion else "",
            "correo": correo.strip().lower() if correo else None,
            "password": generate_password_hash(password) if password else None,
            "roll": nombre.strip(),  # Asignar el rol a sí mismo (admin o usuario)
            "permisos": permisos,
            "estado": estado,
            "activo": True,
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        
        resultado = roles_col.insert_one(nuevo_rol)
        return True, "Rol creado exitosamente", str(resultado.inserted_id)
    
    except Exception as e:
        return False, f"Error al crear rol: {str(e)}", None


def obtener_todos_los_roles():
    """
    Obtiene todos los roles/usuarios de MONGO_COLLECTIONS
    
    Returns:
        list: Lista de roles
    """
    try:
        # Busca documentos que tengan roll: "admin" o "usuario"
        roles = list(roles_col.find({"roll": {"$in": ["admin", "usuario"]}}).sort("fecha_creacion", -1))
        for rol in roles:
            rol["_id"] = str(rol["_id"])
            # Usar roll como nombre si no existe nombre
            if "nombre" not in rol or not rol.get("nombre"):
                rol["nombre"] = rol.get("roll", "sin nombre").capitalize()
            # Convertir fechas a ISO format si existen
            if "fecha_creacion" in rol:
                rol["fecha_creacion"] = rol["fecha_creacion"].isoformat() if isinstance(rol["fecha_creacion"], datetime) else str(rol["fecha_creacion"])
            if "fecha_actualizacion" in rol:
                rol["fecha_actualizacion"] = rol["fecha_actualizacion"].isoformat() if isinstance(rol["fecha_actualizacion"], datetime) else str(rol["fecha_actualizacion"])
            # Agregar estado por defecto si no existe o es None
            if "estado" not in rol or rol.get("estado") is None:
                rol["estado"] = "activo"
        return roles
    except Exception as e:
        print(f"Error al obtener roles: {e}")
        return []


def obtener_rol_por_id(rol_id):
    """
    Obtiene un rol por su ID
    
    Args:
        rol_id (str): ID del rol
    
    Returns:
        dict: Rol encontrado o None
    """
    try:
        rol = roles_col.find_one({"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}})
        if rol:
            rol["_id"] = str(rol["_id"])
            rol["fecha_creacion"] = rol["fecha_creacion"].isoformat() if isinstance(rol["fecha_creacion"], datetime) else str(rol["fecha_creacion"])
            rol["fecha_actualizacion"] = rol["fecha_actualizacion"].isoformat() if isinstance(rol["fecha_actualizacion"], datetime) else str(rol["fecha_actualizacion"])
        return rol
    except Exception as e:
        print(f"Error al obtener rol: {e}")
        return None


def actualizar_rol(rol_id, nombre=None, descripcion=None, permisos=None, estado=None):
    """
    Actualiza un rol existente
    
    Args:
        rol_id (str): ID del rol
        nombre (str): Nuevo nombre
        descripcion (str): Nueva descripción
        permisos (dict): Nuevos permisos
        estado (str): Nuevo estado
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        update_data = {"fecha_actualizacion": datetime.utcnow()}
        
        if nombre:
            # Verificar que no exista otro rol con el mismo nombre
            existe = roles_col.find_one({
                "roll": {"$in": ["admin", "usuario"]},
                "nombre": nombre.lower(),
                "_id": {"$ne": ObjectId(rol_id)}
            })
            if existe:
                return False, "Ya existe otro rol con este nombre"
            update_data["nombre"] = nombre.strip()
        
        if descripcion is not None:
            update_data["descripcion"] = descripcion.strip()
        
        if permisos is not None:
            update_data["permisos"] = permisos
        
        if estado:
            update_data["estado"] = estado
        
        resultado = roles_col.update_one(
            {"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}},
            {"$set": update_data}
        )
        
        if resultado.matched_count == 0:
            return False, "Rol no encontrado"
        
        return True, "Rol actualizado exitosamente"
    
    except Exception as e:
        return False, f"Error al actualizar rol: {str(e)}"


def eliminar_rol(rol_id):
    """
    Elimina un rol (solo si no hay usuarios con este rol)
    
    Args:
        rol_id (str): ID del rol
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        # Verificar si hay usuarios con este rol
        rol = roles_col.find_one({"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}})
        if not rol:
            return False, "Rol no encontrado"
        
        usuarios_con_rol = usuarios_col.find_one({"roll": rol.get("nombre", rol.get("roll")), "correo": {"$exists": True}})
        if usuarios_con_rol:
            return False, f"No se puede eliminar el rol porque hay usuarios asignados a él"
        
        resultado = roles_col.delete_one({"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}})
        
        if resultado.deleted_count == 0:
            return False, "No se pudo eliminar el rol"
        
        return True, "Rol eliminado exitosamente"
    
    except Exception as e:
        return False, f"Error al eliminar rol: {str(e)}"


def asignar_rol_a_usuario(correo, nombre_rol):
    """
    Asigna un rol a un usuario
    
    Args:
        correo (str): Correo del usuario
        nombre_rol (str): Nombre del rol a asignar
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        # Verificar que el usuario existe
        usuario = usuarios_col.find_one({"correo": correo, "tipo": {"$ne": "rol"}})
        if not usuario:
            return False, "Usuario no encontrado"
        
        # Verificar que el rol existe
        rol = roles_col.find_one({"nombre": nombre_rol, "tipo": "rol"})
        if not rol:
            return False, "Rol no encontrado"
        
        # Actualizar el rol del usuario
        usuarios_col.update_one(
            {"correo": correo},
            {"$set": {"roll": nombre_rol}}
        )
        
        return True, f"Rol '{nombre_rol}' asignado a {correo}"
    
    except Exception as e:
        return False, f"Error al asignar rol: {str(e)}"


def obtener_usuarios_por_rol(nombre_rol):
    """
    Obtiene todos los usuarios con un rol específico
    
    Args:
        nombre_rol (str): Nombre del rol
    
    Returns:
        list: Lista de usuarios
    """
    try:
        usuarios = list(usuarios_col.find({"roll": nombre_rol, "correo": {"$exists": True}}))
        for usuario in usuarios:
            usuario["_id"] = str(usuario["_id"])
            # No mostrar contraseña
            usuario.pop("password", None)
        return usuarios
    except Exception as e:
        print(f"Error al obtener usuarios por rol: {e}")
        return []


def obtener_estadisticas_roles():
    """
    Obtiene estadísticas de los roles
    
    Returns:
        dict: Estadísticas
    """
    try:
        total_roles = roles_col.count_documents({"roll": {"$in": ["admin", "usuario"]}})
        roles_activos = roles_col.count_documents({"roll": {"$in": ["admin", "usuario"]}, "estado": "activo"})
        roles_inactivos = roles_col.count_documents({"roll": {"$in": ["admin", "usuario"]}, "estado": "inactivo"})
        
        # Contar usuarios por rol
        roles_list = list(roles_col.find({"roll": {"$in": ["admin", "usuario"]}}))
        estadisticas_por_rol = []
        
        for rol in roles_list:
            cantidad_usuarios = usuarios_col.count_documents({"roll": rol.get("nombre", rol.get("roll")), "correo": {"$exists": True}})
            estadisticas_por_rol.append({
                "nombre": rol.get("nombre", rol.get("roll")),
                "cantidad_usuarios": cantidad_usuarios
            })
        
        return {
            "total_roles": total_roles,
            "roles_activos": roles_activos,
            "roles_inactivos": roles_inactivos,
            "estadisticas_por_rol": estadisticas_por_rol
        }
    
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return {}


def definir_permisos_rol(rol_id, permisos):
    """
    Define los permisos específicos para un rol
    
    Args:
        rol_id (str): ID del rol
        permisos (dict): Diccionario de permisos
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        rol = roles_col.find_one({"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}})
        if not rol:
            return False, "Rol no encontrado"
        
        # Permisos por defecto
        permisos_default = {
            "ver_dashboard": False,
            "registrar_venta": False,
            "ver_analisis": False,
            "generar_respaldos": False,
            "restaurar_respaldos": False,
            "gestionar_usuarios": False,
            "gestionar_roles": False
        }
        
        # Actualizar con los permisos proporcionados
        if isinstance(permisos, dict):
            permisos_default.update(permisos)
        
        resultado = roles_col.update_one(
            {"_id": ObjectId(rol_id), "roll": {"$in": ["admin", "usuario"]}},
            {"$set": {
                "permisos": permisos_default,
                "fecha_actualizacion": datetime.utcnow()
            }}
        )
        
        if resultado.matched_count == 0:
            return False, "Rol no encontrado"
        
        return True, "Permisos actualizados exitosamente"
    
    except Exception as e:
        return False, f"Error al definir permisos: {str(e)}"
