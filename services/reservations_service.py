# services/reservations_service.py
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from db import db

reservations_col = db["MONGO_COLLECTIONS"]


def crear_reservacion(nombre, email, telefono, numero_personas, fecha, hora, notas=""):
    """
    Guarda una nueva reservación en MONGO_COLLECTIONS
    
    Args:
        nombre (str): Nombre del cliente
        email (str): Email del cliente
        telefono (str): Teléfono del cliente
        numero_personas (str): Número de personas
        fecha (str): Fecha de reservación (formato YYYY-MM-DD)
        hora (str): Hora de reservación (formato HH:MM)
        notas (str): Notas especiales (opcional)
    
    Returns:
        (success: bool, mensaje: str, reserva_id: str)
    """
    try:
        if not all([nombre, email, telefono, numero_personas, fecha, hora]):
            return False, "Todos los campos obligatorios deben completarse", None
        
        # Validar email
        if '@' not in email or '.' not in email:
            return False, "Email inválido", None
        
        nueva_reservacion = {
            "tipo": "reservacion",  # Campo para distinguir reservaciones
            "nombre": nombre.strip(),
            "email": email.strip().lower(),
            "telefono": telefono.strip(),
            "numero_personas": numero_personas,
            "fecha": fecha,
            "hora": hora,
            "notas": notas.strip() if notas else "",
            "estado": "pendiente",  # pendiente, confirmada, cancelada
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        
        resultado = reservations_col.insert_one(nueva_reservacion)
        return True, "Reservación guardada exitosamente", str(resultado.inserted_id)
    
    except Exception as e:
        return False, f"Error al guardar reservación: {str(e)}", None


def obtener_todas_las_reservaciones():
    """
    Obtiene todas las reservaciones de MONGO_COLLECTIONS
    
    Returns:
        list: Lista de reservaciones ordenadas por fecha
    """
    try:
        reservaciones = list(reservations_col.find({"tipo": "reservacion"}).sort("fecha", -1).sort("hora", -1))
        for reservación in reservaciones:
            reservación["_id"] = str(reservación["_id"])
            if isinstance(reservación.get("fecha_creacion"), datetime):
                reservación["fecha_creacion"] = reservación["fecha_creacion"].isoformat()
            if isinstance(reservación.get("fecha_actualizacion"), datetime):
                reservación["fecha_actualizacion"] = reservación["fecha_actualizacion"].isoformat()
        return reservaciones
    except Exception as e:
        print(f"Error al obtener reservaciones: {e}")
        return []


def obtener_reservacion_por_id(reserva_id):
    """
    Obtiene una reservación por su ID de MONGO_COLLECTIONS
    
    Args:
        reserva_id (str): ID de la reservación
    
    Returns:
        dict: Reservación encontrada o None
    """
    try:
        reservacion = reservations_col.find_one({"_id": ObjectId(reserva_id), "tipo": "reservacion"})
        if reservacion:
            reservacion["_id"] = str(reservacion["_id"])
            if isinstance(reservacion.get("fecha_creacion"), datetime):
                reservacion["fecha_creacion"] = reservacion["fecha_creacion"].isoformat()
            if isinstance(reservacion.get("fecha_actualizacion"), datetime):
                reservacion["fecha_actualizacion"] = reservacion["fecha_actualizacion"].isoformat()
        return reservacion
    except Exception as e:
        print(f"Error al obtener reservación: {e}")
        return None


def actualizar_estado_reservacion(reserva_id, nuevo_estado):
    """
    Actualiza el estado de una reservación en MONGO_COLLECTIONS
    
    Args:
        reserva_id (str): ID de la reservación
        nuevo_estado (str): Nuevo estado (pendiente, confirmada, cancelada)
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        if nuevo_estado not in ["pendiente", "confirmada", "cancelada"]:
            return False, "Estado inválido"
        
        resultado = reservations_col.update_one(
            {"_id": ObjectId(reserva_id), "tipo": "reservacion"},
            {"$set": {
                "estado": nuevo_estado,
                "fecha_actualizacion": datetime.utcnow()
            }}
        )
        
        if resultado.matched_count == 0:
            return False, "Reservación no encontrada"
        
        return True, f"Reservación actualizada a '{nuevo_estado}'"
    
    except Exception as e:
        return False, f"Error al actualizar reservación: {str(e)}"


def eliminar_reservacion(reserva_id):
    """
    Elimina una reservación de MONGO_COLLECTIONS
    
    Args:
        reserva_id (str): ID de la reservación
    
    Returns:
        (success: bool, mensaje: str)
    """
    try:
        resultado = reservations_col.delete_one({"_id": ObjectId(reserva_id), "tipo": "reservacion"})
        
        if resultado.deleted_count == 0:
            return False, "Reservación no encontrada"
        
        return True, "Reservación eliminada"
    
    except Exception as e:
        return False, f"Error al eliminar reservación: {str(e)}"


def obtener_estadisticas_reservaciones():
    """
    Obtiene estadísticas de las reservaciones de MONGO_COLLECTIONS
    
    Returns:
        dict: Estadísticas
    """
    try:
        total = reservations_col.count_documents({"tipo": "reservacion"})
        pendientes = reservations_col.count_documents({"tipo": "reservacion", "estado": "pendiente"})
        confirmadas = reservations_col.count_documents({"tipo": "reservacion", "estado": "confirmada"})
        canceladas = reservations_col.count_documents({"tipo": "reservacion", "estado": "cancelada"})
        
        # Calcular total de personas reservadas
        todas = obtener_todas_las_reservaciones()
        total_personas = sum(int(r.get("numero_personas", 0)) for r in todas)
        
        return {
            "total": total,
            "pendientes": pendientes,
            "confirmadas": confirmadas,
            "canceladas": canceladas,
            "total_personas": total_personas
        }
    
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return {}


def obtener_reservaciones_por_estatus(estado):
    """
    Obtiene reservaciones por estado específico de MONGO_COLLECTIONS
    
    Args:
        estado (str): Estado a filtrar (pendiente, confirmada, cancelada)
    
    Returns:
        list: Lista de reservaciones
    """
    try:
        reservaciones = list(reservations_col.find({"tipo": "reservacion", "estado": estado}).sort("fecha", -1))
        for reservación in reservaciones:
            reservación["_id"] = str(reservación["_id"])
        return reservaciones
    except Exception as e:
        print(f"Error al obtener reservaciones por estado: {e}")
        return []
