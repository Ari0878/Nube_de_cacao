# services/scheduler_service.py
import os
import schedule
import time
import threading
from datetime import datetime
from services.backup_service import exportar_excel, exportar_pdf, exportar_sql
from db import db

# Configuración de carpeta de respaldos
BACKUP_FOLDER = "backups_automaticos"

# Crear carpeta si no existe
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)


def realizar_respaldo_automatico(formato="todos"):
    """
    Realiza un respaldo automático en el formato especificado.
    
    Args:
        formato (str): "excel", "pdf", "sql" o "todos"
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato in ["excel", "todos"]:
            archivo_excel = exportar_excel()
            if archivo_excel:
                ruta_excel = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.xlsx")
                with open(ruta_excel, 'wb') as f:
                    f.write(archivo_excel.read())
                print(f"✅ Respaldo Excel creado: {ruta_excel}")
        
        if formato in ["pdf", "todos"]:
            archivo_pdf = exportar_pdf()
            if archivo_pdf:
                ruta_pdf = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.pdf")
                with open(ruta_pdf, 'wb') as f:
                    f.write(archivo_pdf.read())
                print(f"✅ Respaldo PDF creado: {ruta_pdf}")
        
        if formato in ["sql", "todos"]:
            archivo_sql = exportar_sql()
            if archivo_sql:
                ruta_sql = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.sql")
                with open(ruta_sql, 'wb') as f:
                    f.write(archivo_sql.read())
                print(f"✅ Respaldo SQL creado: {ruta_sql}")
        
        # Guardar registro en MongoDB
        registrar_respaldo_en_db(timestamp, formato)
        
    except Exception as e:
        print(f"❌ Error al realizar respaldo automático: {e}")


def registrar_respaldo_en_db(timestamp, formato):
    """Registra el respaldo realizado en la base de datos"""
    try:
        if db is not None:
            respaldos_col = db["respaldos_automaticos"]
            respaldos_col.insert_one({
                "fecha": datetime.now(),
                "timestamp": timestamp,
                "formato": formato,
                "tipo": "automatico"
            })
    except Exception as e:
        print(f"Error al registrar respaldo en DB: {e}")


def limpiar_respaldos_antiguos(dias=30):
    """
    Elimina respaldos automáticos con más de X días de antigüedad.
    
    Args:
        dias (int): Número de días a mantener
    """
    try:
        ahora = time.time()
        limite = dias * 86400  # días en segundos
        
        archivos_eliminados = 0
        for archivo in os.listdir(BACKUP_FOLDER):
            ruta_archivo = os.path.join(BACKUP_FOLDER, archivo)
            if os.path.isfile(ruta_archivo):
                tiempo_creacion = os.path.getctime(ruta_archivo)
                if ahora - tiempo_creacion > limite:
                    os.remove(ruta_archivo)
                    archivos_eliminados += 1
        
        if archivos_eliminados > 0:
            print(f"🗑️ Se eliminaron {archivos_eliminados} respaldos antiguos (>{dias} días)")
    
    except Exception as e:
        print(f"Error al limpiar respaldos antiguos: {e}")


def configurar_respaldos_automaticos(config):
    """
    Configura los respaldos automáticos según la configuración proporcionada.
    
    Args:
        config (dict): Diccionario con la configuración
            {
                "activo": True/False,
                "hora": "14:30",  # Formato 24h
                "frecuencia": "diario",  # "diario", "semanal", "mensual"
                "dia_semana": "monday",  # Para frecuencia semanal
                "dia_mes": 1,  # Para frecuencia mensual
                "formato": "todos",  # "excel", "pdf", "sql", "todos"
                "limpiar_antiguos": True,
                "dias_retener": 30
            }
    """
    schedule.clear()  # Limpiar trabajos anteriores
    
    if not config.get("activo", False):
        print("⏸️ Respaldos automáticos desactivados")
        return
    
    hora = config.get("hora", "02:00")
    frecuencia = config.get("frecuencia", "diario")
    formato = config.get("formato", "todos")
    
    # Configurar tarea de respaldo
    if frecuencia == "diario":
        schedule.every().day.at(hora).do(realizar_respaldo_automatico, formato=formato)
        print(f"📅 Respaldo diario configurado a las {hora}")
    
    elif frecuencia == "semanal":
        dia_semana = config.get("dia_semana", "monday")
        getattr(schedule.every(), dia_semana).at(hora).do(realizar_respaldo_automatico, formato=formato)
        print(f"📅 Respaldo semanal configurado los {dia_semana} a las {hora}")
    
    elif frecuencia == "mensual":
        # Para mensual, verificamos cada día si es el día correcto
        schedule.every().day.at(hora).do(verificar_respaldo_mensual, config)
        print(f"📅 Respaldo mensual configurado el día {config.get('dia_mes', 1)} a las {hora}")
    
    # Configurar limpieza de respaldos antiguos (diaria a las 3 AM)
    if config.get("limpiar_antiguos", True):
        dias_retener = config.get("dias_retener", 30)
        schedule.every().day.at("03:00").do(limpiar_respaldos_antiguos, dias=dias_retener)
        print(f"🗑️ Limpieza automática configurada (retener últimos {dias_retener} días)")


def verificar_respaldo_mensual(config):
    """Verifica si hoy es el día del mes configurado para hacer respaldo"""
    dia_actual = datetime.now().day
    dia_configurado = config.get("dia_mes", 1)
    
    if dia_actual == dia_configurado:
        formato = config.get("formato", "todos")
        realizar_respaldo_automatico(formato=formato)


def ejecutar_scheduler():
    """Ejecuta el scheduler en un hilo separado"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto


# Hilo global para el scheduler
scheduler_thread = None


def iniciar_scheduler(config):
    """
    Inicia el scheduler en un hilo separado.
    
    Args:
        config (dict): Configuración de respaldos automáticos
    """
    global scheduler_thread
    
    configurar_respaldos_automaticos(config)
    
    if scheduler_thread is None or not scheduler_thread.is_alive():
        scheduler_thread = threading.Thread(target=ejecutar_scheduler, daemon=True)
        scheduler_thread.start()
        print("🚀 Scheduler de respaldos iniciado")


def detener_scheduler():
    """Detiene el scheduler"""
    schedule.clear()
    print("⏹️ Scheduler de respaldos detenido")


def obtener_proximos_respaldos():
    """Retorna información sobre los próximos respaldos programados"""
    try:
        jobs = schedule.get_jobs()
        proximos = []
        
        for job in jobs:
            # Identificar el tipo de tarea de forma amigable
            nombre_funcion = str(job.job_func)
            
            if "realizar_respaldo_automatico" in nombre_funcion:
                # Extraer el formato del respaldo
                if "formato='todos'" in nombre_funcion:
                    descripcion = "📦 Respaldo completo (Excel, PDF y SQL)"
                elif "formato='excel'" in nombre_funcion:
                    descripcion = "📗 Respaldo en Excel"
                elif "formato='pdf'" in nombre_funcion:
                    descripcion = "📕 Respaldo en PDF"
                elif "formato='sql'" in nombre_funcion:
                    descripcion = "💾 Respaldo en SQL"
                else:
                    descripcion = "📦 Respaldo de base de datos"
            
            elif "limpiar_respaldos_antiguos" in nombre_funcion:
                descripcion = "🗑️ Limpieza de respaldos antiguos"
            
            elif "verificar_respaldo_mensual" in nombre_funcion:
                descripcion = "📅 Verificación de respaldo mensual"
            
            else:
                descripcion = "⚙️ Tarea programada"
            
            proximos.append({
                "tarea": descripcion,
                "proxima_ejecucion": job.next_run.strftime("%d/%m/%Y %H:%M") if job.next_run else "N/A",
                "proxima_ejecucion_completa": job.next_run.strftime("%Y-%m-%d %H:%M:%S") if job.next_run else "N/A"
            })
        
        return proximos
    except Exception as e:
        print(f"Error al obtener próximos respaldos: {e}")
        return []


def obtener_historial_respaldos(limite=50):
    """Obtiene el historial de respaldos automáticos realizados"""
    try:
        if db is None:
            return []
        
        respaldos_col = db["respaldos_automaticos"]
        historial = list(respaldos_col.find().sort("fecha", -1).limit(limite))
        
        for item in historial:
            item["_id"] = str(item["_id"])
            if "fecha" in item and isinstance(item["fecha"], datetime):
                item["fecha"] = item["fecha"].strftime("%Y-%m-%d %H:%M:%S")
        
        return historial
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []


def guardar_configuracion(config):
    """Guarda la configuración de respaldos en la base de datos"""
    try:
        if db is None:
            return False
        
        config_col = db["configuracion_respaldos"]
        
        # Actualizar o insertar configuración
        config_col.update_one(
            {"tipo": "configuracion_principal"},
            {"$set": {**config, "actualizado": datetime.now()}},
            upsert=True
        )
        
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False


def cargar_configuracion():
    """Carga la configuración de respaldos desde la base de datos"""
    try:
        if db is None:
            return get_configuracion_default()
        
        config_col = db["configuracion_respaldos"]
        config = config_col.find_one({"tipo": "configuracion_principal"})
        
        if config:
            config.pop("_id", None)
            config.pop("tipo", None)
            config.pop("actualizado", None)
            return config
        else:
            return get_configuracion_default()
    
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
        return get_configuracion_default()


def get_configuracion_default():
    """Retorna la configuración por defecto"""
    return {
        "activo": False,
        "hora": "02:00",
        "frecuencia": "diario",
        "dia_semana": "monday",
        "dia_mes": 1,
        "formato": "todos",
        "limpiar_antiguos": True,
        "dias_retener": 30
    }