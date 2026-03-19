# services/scheduler_service.py
import os
import schedule
import time
import threading
from datetime import datetime
from db import cursor, conn

# Configuración de carpeta de respaldos
BACKUP_FOLDER = "backups_automaticos"

# Crear carpeta si no existe
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)


def realizar_respaldo_automatico(formato="todos"):
    """
    Realiza un respaldo automático en el formato especificado.
    """
    try:
        # Importar funciones de respaldo
        from services.backup_service import (
            generar_backup_completo,
            generar_excel,
            generar_pdf,
            generar_sql
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tipo_respaldo = "completo"
        
        # Obtener datos
        tablas, total_registros = generar_backup_completo()
        
        if not tablas:
            print("❌ No hay datos para respaldar")
            return
        
        archivos_generados = []
        
        if formato in ["excel", "todos"]:
            archivo_excel = generar_excel(tablas, tipo_respaldo)
            if archivo_excel:
                ruta_excel = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.xlsx")
                with open(ruta_excel, 'wb') as f:
                    f.write(archivo_excel.getvalue())
                archivos_generados.append(ruta_excel)
                print(f"✅ Respaldo Excel creado: {ruta_excel}")
        
        if formato in ["pdf", "todos"]:
            archivo_pdf = generar_pdf(tablas, tipo_respaldo)
            if archivo_pdf:
                ruta_pdf = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.pdf")
                with open(ruta_pdf, 'wb') as f:
                    f.write(archivo_pdf.getvalue())
                archivos_generados.append(ruta_pdf)
                print(f"✅ Respaldo PDF creado: {ruta_pdf}")
        
        if formato in ["sql", "todos"]:
            archivo_sql = generar_sql(tablas, tipo_respaldo)
            if archivo_sql:
                ruta_sql = os.path.join(BACKUP_FOLDER, f"auto_backup_{timestamp}.sql")
                with open(ruta_sql, 'wb') as f:
                    f.write(archivo_sql.getvalue())
                archivos_generados.append(ruta_sql)
                print(f"✅ Respaldo SQL creado: {ruta_sql}")
        
        # Registrar respaldo en MySQL
        registrar_respaldo_en_db(timestamp, formato, len(archivos_generados), total_registros)
        
    except Exception as e:
        print(f"❌ Error al realizar respaldo automático: {e}")
        import traceback
        traceback.print_exc()


def registrar_respaldo_en_db(timestamp, formato, num_archivos, total_registros):
    """Registra el respaldo realizado en MySQL"""
    try:
        if cursor is None or conn is None:
            print("⚠️ No hay conexión a MySQL para registrar respaldo")
            return
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS respaldos_automaticos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha DATETIME,
                timestamp VARCHAR(50),
                formato VARCHAR(50),
                num_archivos INT,
                total_registros INT,
                tipo VARCHAR(50)
            )
        """)
        
        query = """
            INSERT INTO respaldos_automaticos 
            (fecha, timestamp, formato, num_archivos, total_registros, tipo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (datetime.now(), timestamp, formato, num_archivos, total_registros, "automatico")
        
        cursor.execute(query, valores)
        conn.commit()
        
    except Exception as e:
        print(f"Error al registrar respaldo en DB: {e}")


def limpiar_respaldos_antiguos(dias=30):
    """
    Elimina respaldos automáticos con más de X días de antigüedad.
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
    Configura los respaldos automáticos según la configuración.
    """
    schedule.clear()  # Limpiar trabajos anteriores
    
    if not config.get("activo", False):
        print("⏸️ Respaldos automáticos desactivados")
        return
    
    hora = config.get("hora", "02:00")
    frecuencia = config.get("frecuencia", "diario")
    formato = config.get("formato", "todos")
    
    if frecuencia == "diario":
        schedule.every().day.at(hora).do(realizar_respaldo_automatico, formato=formato)
        print(f"📅 Respaldo diario configurado a las {hora}")
    
    elif frecuencia == "semanal":
        dia_semana = config.get("dia_semana", "monday")
        getattr(schedule.every(), dia_semana).at(hora).do(realizar_respaldo_automatico, formato=formato)
        print(f"📅 Respaldo semanal configurado los {dia_semana} a las {hora}")
    
    elif frecuencia == "mensual":
        schedule.every().day.at(hora).do(verificar_respaldo_mensual, config)
        print(f"📅 Respaldo mensual configurado el día {config.get('dia_mes', 1)} a las {hora}")
    
    # Configurar limpieza
    if config.get("limpiar_antiguos", True):
        dias_retener = config.get("dias_retener", 30)
        schedule.every().day.at("03:00").do(limpiar_respaldos_antiguos, dias=dias_retener)
        print(f"🗑️ Limpieza automática configurada (retener últimos {dias_retener} días)")


def verificar_respaldo_mensual(config):
    """Verifica si hoy es el día del mes configurado"""
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


# Hilo global
scheduler_thread = None


def iniciar_scheduler(config):
    """
    Inicia el scheduler en un hilo separado.
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
            nombre_funcion = str(job.job_func)
            
            if "realizar_respaldo_automatico" in nombre_funcion:
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
            })
        
        return proximos
    except Exception as e:
        print(f"Error al obtener próximos respaldos: {e}")
        return []


def obtener_historial_respaldos(limite=50):
    """Obtiene el historial de respaldos automáticos desde MySQL"""
    try:
        if cursor is None:
            return []
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS respaldos_automaticos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha DATETIME,
                timestamp VARCHAR(50),
                formato VARCHAR(50),
                num_archivos INT,
                total_registros INT,
                tipo VARCHAR(50)
            )
        """)
        
        cursor.execute("""
            SELECT * FROM respaldos_automaticos 
            ORDER BY fecha DESC 
            LIMIT %s
        """, (limite,))
        
        historial = cursor.fetchall()
        
        # Formatear fechas
        for item in historial:
            if item.get("fecha") and isinstance(item["fecha"], datetime):
                item["fecha"] = item["fecha"].strftime("%Y-%m-%d %H:%M:%S")
        
        return historial
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []


def guardar_configuracion(config):
    """Guarda la configuración de respaldos en MySQL"""
    try:
        if cursor is None or conn is None:
            return False
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion_respaldos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50),
                configuracion JSON,
                actualizado DATETIME
            )
        """)
        
        # Convertir config a JSON
        import json
        config_json = json.dumps(config)
        
        # Verificar si ya existe
        cursor.execute("SELECT id FROM configuracion_respaldos WHERE tipo = 'configuracion_principal'")
        existe = cursor.fetchone()
        
        if existe:
            query = """
                UPDATE configuracion_respaldos 
                SET configuracion = %s, actualizado = %s 
                WHERE tipo = 'configuracion_principal'
            """
        else:
            query = """
                INSERT INTO configuracion_respaldos (tipo, configuracion, actualizado)
                VALUES ('configuracion_principal', %s, %s)
            """
        
        cursor.execute(query, (config_json, datetime.now()))
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False


def cargar_configuracion():
    """Carga la configuración de respaldos desde MySQL"""
    try:
        if cursor is None:
            return get_configuracion_default()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion_respaldos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50),
                configuracion JSON,
                actualizado DATETIME
            )
        """)
        
        cursor.execute("SELECT configuracion FROM configuracion_respaldos WHERE tipo = 'configuracion_principal'")
        resultado = cursor.fetchone()
        
        if resultado and resultado.get("configuracion"):
            import json
            return json.loads(resultado["configuracion"])
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