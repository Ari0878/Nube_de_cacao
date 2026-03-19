# services/auto_backup_service.py
import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import cursor, conn

# Directorio para configuración de respaldos automáticos
AUTO_BACKUP_DIR = "auto_backup_config"
BACKUPS_STORAGE_DIR = "backups_automaticos"

# Crear directorios
for directory in [AUTO_BACKUP_DIR, BACKUPS_STORAGE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

CONFIG_FILE = os.path.join(AUTO_BACKUP_DIR, "config.json")
HISTORIAL_FILE = os.path.join(AUTO_BACKUP_DIR, "historial.json")

# Scheduler global
scheduler = BackgroundScheduler()
scheduler.start()


def obtener_todas_tablas():
    """
    Obtiene todas las tablas de la base de datos
    """
    tablas = {}
    
    if cursor is None:
        print("Error: No hay conexión a la base de datos")
        return tablas
    
    try:
        cursor.execute("SHOW TABLES")
        tablas_nombres = cursor.fetchall()
        
        for tabla_item in tablas_nombres:
            nombre_tabla = list(tabla_item.values())[0]
            
            try:
                cursor.execute(f"SELECT * FROM {nombre_tabla}")
                filas = cursor.fetchall()
                
                # Convertir fechas
                filas_procesadas = []
                for fila in filas:
                    fila_dict = {}
                    for key, value in fila.items():
                        if isinstance(value, datetime):
                            fila_dict[key] = value.isoformat()
                        else:
                            fila_dict[key] = value
                    filas_procesadas.append(fila_dict)
                
                tablas[nombre_tabla] = filas_procesadas
                
            except Exception as e:
                print(f"Error obteniendo datos de {nombre_tabla}: {e}")
                continue
    
    except Exception as e:
        print(f"Error al obtener tablas: {e}")
    
    return tablas


def cargar_config():
    """Carga la configuración de respaldos automáticos"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Configuración por defecto
    return {
        "activo": False,
        "hora": "02:00",
        "frecuencia": "diario",
        "dia_semana": "monday",
        "dia_mes": 1,
        "formato": "todos",
        "limpiar_antiguos": True,
        "dias_retener": 30,
        "tipo_respaldo": "completo"
    }


def guardar_config(config):
    """Guarda la configuración"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def cargar_historial():
    """Carga el historial de respaldos automáticos"""
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def guardar_historial(historial):
    """Guarda el historial"""
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def agregar_historial(tipo_respaldo, formato, cantidad_registros, tablas_respaldadas, archivos_generados=None, estado="exitoso"):
    """Agrega una entrada al historial"""
    historial = cargar_historial()
    
    entrada = {
        "fecha": datetime.now().isoformat(),
        "tipo_respaldo": tipo_respaldo,
        "formato": formato,
        "cantidad_registros": cantidad_registros,
        "tablas": tablas_respaldadas,
        "archivos": archivos_generados or [],
        "estado": estado
    }
    
    historial.insert(0, entrada)
    
    # Mantener últimos 100
    if len(historial) > 100:
        historial = historial[:100]
    
    guardar_historial(historial)


def obtener_proximos_respaldos():
    """Calcula las próximas 5 ejecuciones programadas"""
    config = cargar_config()
    
    if not config.get("activo"):
        return []
    
    proximos = []
    
    # Parsear hora
    try:
        hora_partes = config["hora"].split(":")
        hour = int(hora_partes[0])
        minute = int(hora_partes[1])
    except:
        hour, minute = 2, 0
    
    ahora = datetime.now()
    
    tipo_respaldo = config.get("tipo_respaldo", "completo").capitalize()
    formato = config.get("formato", "todos").upper()
    
    if config["frecuencia"] == "diario":
        # Próximos 5 días
        for i in range(5):
            fecha = ahora + timedelta(days=i)
            fecha = fecha.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if fecha > ahora:
                proximos.append({
                    "tarea": f"Respaldo {tipo_respaldo} Diario ({formato})",
                    "proxima_ejecucion": fecha.strftime("%Y-%m-%d %H:%M")
                })
            
            if len(proximos) >= 5:
                break
    
    elif config["frecuencia"] == "semanal":
        dias_semana = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        dia_objetivo = dias_semana.get(config.get("dia_semana", "monday"), 0)
        
        for i in range(10):
            dias_hasta = (dia_objetivo - ahora.weekday() + 7 * i) % 7
            if dias_hasta == 0 and i == 0:
                dias_hasta = 7
            
            fecha = ahora + timedelta(days=dias_hasta)
            fecha = fecha.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if fecha > ahora:
                proximos.append({
                    "tarea": f"Respaldo {tipo_respaldo} Semanal ({formato})",
                    "proxima_ejecucion": fecha.strftime("%Y-%m-%d %H:%M")
                })
            
            if len(proximos) >= 5:
                break
    
    elif config["frecuencia"] == "mensual":
        dia_mes = config.get("dia_mes", 1)
        
        for i in range(12):
            try:
                mes = ahora.month + i
                año = ahora.year + (mes - 1) // 12
                mes = ((mes - 1) % 12) + 1
                
                fecha = datetime(año, mes, min(dia_mes, 28), hour, minute)
                
                if fecha > ahora:
                    proximos.append({
                        "tarea": f"Respaldo {tipo_respaldo} Mensual ({formato})",
                        "proxima_ejecucion": fecha.strftime("%Y-%m-%d %H:%M")
                    })
                
                if len(proximos) >= 5:
                    break
            except:
                continue
    
    return proximos


def ejecutar_respaldo_programado():
    """
    Función que se ejecuta automáticamente según el horario.
    """
    from services.backup_service import generar_excel, generar_pdf, generar_sql
    from services.email_service import enviar_email_respaldo, cargar_config_email
    
    config = cargar_config()
    
    if not config.get("activo"):
        return
    
    try:
        print("Iniciando respaldo automático...")
        
        # Obtener todas las tablas
        tablas = obtener_todas_tablas()
        if not tablas:
            print("No se encontraron tablas para respaldar")
            agregar_historial(
                config.get("tipo_respaldo", "completo"), 
                config.get("formato", "todos"), 
                0, {}, [], 
                "error: No se encontraron tablas"
            )
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formato_config = config.get("formato", "todos")
        tipo_respaldo = config.get("tipo_respaldo", "completo")
        
        total_registros = sum(len(datos) for datos in tablas.values())
        tablas_respaldadas = {nombre: len(datos) for nombre, datos in tablas.items()}
        
        archivos_generados = []
        archivos_paths = []
        
        # Generar archivos
        if formato_config == "todos" or formato_config == "excel":
            archivo_excel = generar_excel(tablas, tipo_respaldo)
            filename = f"backup_auto_{tipo_respaldo}_{timestamp}.xlsx"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_excel.getvalue())
            
            archivos_generados.append(filename)
            archivos_paths.append(filepath)
            print(f"  Excel generado: {filename}")
        
        if formato_config == "todos" or formato_config == "pdf":
            archivo_pdf = generar_pdf(tablas, tipo_respaldo)
            filename = f"backup_auto_{tipo_respaldo}_{timestamp}.pdf"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_pdf.getvalue())
            
            archivos_generados.append(filename)
            archivos_paths.append(filepath)
            print(f"  PDF generado: {filename}")
        
        if formato_config == "todos" or formato_config == "sql":
            archivo_sql = generar_sql(tablas, tipo_respaldo)
            filename = f"backup_auto_{tipo_respaldo}_{timestamp}.sql"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_sql.getvalue())
            
            archivos_generados.append(filename)
            archivos_paths.append(filepath)
            print(f"  SQL generado: {filename}")
        
        # Registrar en historial
        agregar_historial(
            tipo_respaldo, 
            formato_config, 
            total_registros, 
            tablas_respaldadas, 
            archivos_generados, 
            "exitoso"
        )
        
        print(f"Respaldo automático completado: {total_registros} registros")
        
        # Enviar por correo si está configurado
        try:
            from services.email_service import cargar_config_email, enviar_email_respaldo
            email_config = cargar_config_email()
            if email_config.get("activo", False):
                print(f"Enviando respaldo por correo...")
                success, mensaje = enviar_email_respaldo(
                    archivos_paths,
                    tipo_respaldo,
                    total_registros,
                    tablas_respaldadas
                )
                if success:
                    print(f"   Correo enviado")
                else:
                    print(f"   Error al enviar correo: {mensaje}")
        except Exception as e:
            print(f"   Error al enviar correo: {e}")
        
        # Limpiar archivos antiguos
        if config.get("limpiar_antiguos", False):
            limpiar_backups_antiguos(config.get("dias_retener", 30))
        
    except Exception as e:
        print(f"Error en respaldo automático: {e}")
        import traceback
        traceback.print_exc()
        agregar_historial(
            config.get("tipo_respaldo", "completo"), 
            config.get("formato", "todos"), 
            0, {}, [], 
            f"error: {str(e)}"
        )


def limpiar_backups_antiguos(dias_retener=30):
    """Elimina archivos de respaldo antiguos"""
    try:
        ahora = datetime.now()
        limite = ahora - timedelta(days=dias_retener)
        
        archivos_eliminados = 0
        
        for filename in os.listdir(BACKUPS_STORAGE_DIR):
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            if os.path.isfile(filepath):
                fecha_mod = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if fecha_mod < limite:
                    os.remove(filepath)
                    archivos_eliminados += 1
        
        if archivos_eliminados > 0:
            print(f"Limpieza: {archivos_eliminados} archivo(s) eliminado(s)")
        
    except Exception as e:
        print(f"Error al limpiar archivos: {e}")


def listar_archivos_guardados():
    """Lista todos los archivos de respaldo guardados"""
    archivos = []
    ahora = datetime.now()
    
    try:
        if not os.path.exists(BACKUPS_STORAGE_DIR):
            return archivos
        
        for filename in os.listdir(BACKUPS_STORAGE_DIR):
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            if os.path.isfile(filepath):
                try:
                    stat = os.stat(filepath)
                    fecha_mod = datetime.fromtimestamp(stat.st_mtime)
                    
                    es_nuevo = (ahora - fecha_mod).total_seconds() < 3600
                    
                    # Detectar tipo
                    if 'auto_completo' in filename:
                        tipo_respaldo = "Completo Automático"
                        tipo_color = "primary"
                    elif 'auto_incremental' in filename:
                        tipo_respaldo = "Incremental Automático"
                        tipo_color = "warning"
                    elif 'auto_diferencial' in filename:
                        tipo_respaldo = "Diferencial Automático"
                        tipo_color = "secondary"
                    elif 'manual' in filename:
                        tipo_respaldo = "Manual"
                        tipo_color = "info"
                    elif 'completo' in filename:
                        tipo_respaldo = "Completo"
                        tipo_color = "primary"
                    elif 'incremental' in filename:
                        tipo_respaldo = "Incremental"
                        tipo_color = "warning"
                    elif 'diferencial' in filename:
                        tipo_respaldo = "Diferencial"
                        tipo_color = "secondary"
                    else:
                        tipo_respaldo = "Respaldo"
                        tipo_color = "dark"
                    
                    archivos.append({
                        "nombre": filename,
                        "ruta": filepath,
                        "tamaño": stat.st_size,
                        "tamaño_mb": round(stat.st_size / (1024 * 1024), 2),
                        "fecha": fecha_mod.strftime("%Y-%m-%d %H:%M:%S"),
                        "extension": filename.split('.')[-1].upper(),
                        "es_nuevo": es_nuevo,
                        "tipo_respaldo": tipo_respaldo,
                        "tipo_color": tipo_color
                    })
                except Exception as e:
                    print(f"Error procesando {filename}: {e}")
                    continue
        
        archivos.sort(key=lambda x: x["fecha"], reverse=True)
        
    except Exception as e:
        print(f"Error al listar archivos: {e}")
    
    return archivos


def eliminar_archivo(filename):
    """Elimina un archivo de respaldo específico"""
    try:
        filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
        
        if os.path.exists(filepath) and os.path.isfile(filepath):
            os.remove(filepath)
            return True, "Archivo eliminado exitosamente"
        else:
            return False, "Archivo no encontrado"
    
    except Exception as e:
        return False, f"Error al eliminar: {str(e)}"


def obtener_estadisticas_storage():
    """Obtiene estadísticas del almacenamiento de respaldos"""
    try:
        archivos = listar_archivos_guardados()
        
        total_archivos = len(archivos)
        tamaño_total = sum(a["tamaño"] for a in archivos)
        tamaño_total_mb = round(tamaño_total / (1024 * 1024), 2)
        
        por_tipo = {}
        for archivo in archivos:
            ext = archivo["extension"]
            por_tipo[ext] = por_tipo.get(ext, 0) + 1
        
        return {
            "total_archivos": total_archivos,
            "tamaño_total_mb": tamaño_total_mb,
            "por_tipo": por_tipo,
            "ultimo_respaldo": archivos[0]["fecha"] if archivos else None
        }
    
    except Exception as e:
        return {
            "total_archivos": 0,
            "tamaño_total_mb": 0,
            "por_tipo": {},
            "ultimo_respaldo": None
        }


def configurar_scheduler():
    """Configura el scheduler según la configuración"""
    config = cargar_config()
    
    scheduler.remove_all_jobs()
    
    if not config.get("activo"):
        print("ℹ️ Respaldos automáticos desactivados")
        return
    
    # Parsear hora
    try:
        hora_partes = config["hora"].split(":")
        hour = int(hora_partes[0])
        minute = int(hora_partes[1])
    except:
        hour, minute = 2, 0
    
    if config["frecuencia"] == "diario":
        trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.add_job(
            ejecutar_respaldo_programado,
            trigger=trigger,
            id='backup_diario',
            replace_existing=True
        )
        print(f"✅ Respaldo diario programado a las {hour:02d}:{minute:02d}")
    
    elif config["frecuencia"] == "semanal":
        dias_semana = {
            "monday": "mon", "tuesday": "tue", "wednesday": "wed",
            "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun"
        }
        
        dia = dias_semana.get(config.get("dia_semana", "monday"), "mon")
        trigger = CronTrigger(day_of_week=dia, hour=hour, minute=minute)
        scheduler.add_job(
            ejecutar_respaldo_programado,
            trigger=trigger,
            id='backup_semanal',
            replace_existing=True
        )
        print(f"✅ Respaldo semanal programado: {dia} a las {hour:02d}:{minute:02d}")
    
    elif config["frecuencia"] == "mensual":
        dia_mes = config.get("dia_mes", 1)
        trigger = CronTrigger(day=dia_mes, hour=hour, minute=minute)
        scheduler.add_job(
            ejecutar_respaldo_programado,
            trigger=trigger,
            id='backup_mensual',
            replace_existing=True
        )
        print(f"✅ Respaldo mensual programado: día {dia_mes} a las {hour:02d}:{minute:02d}")


def obtener_estadisticas_historial():
    """Obtiene estadísticas del historial"""
    historial = cargar_historial()
    
    if not historial:
        return {
            "total_respaldos": 0,
            "exitosos": 0,
            "fallidos": 0,
            "ultimo_respaldo": None,
            "total_registros": 0,
            "promedio_registros": 0
        }

    def _to_int(value):
        """Convierte un valor a entero de forma segura."""
        if isinstance(value, int):
            return value
        if isinstance(value, (float, str)):
            try:
                return int(value)
            except Exception:
                return 0
        if isinstance(value, (list, tuple, dict, set)):
            return len(value)
        return 0
    
    exitosos = sum(1 for h in historial if h.get("estado") == "exitoso")
    fallidos = len(historial) - exitosos

    total_registros = sum(
        _to_int(h.get("cantidad_registros", 0))
        for h in historial
        if h.get("estado") == "exitoso"
    )
    
    promedio_registros = total_registros // exitosos if exitosos > 0 else 0
    
    return {
        "total_respaldos": len(historial),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "ultimo_respaldo": historial[0].get("fecha") if historial else None,
        "total_registros": total_registros,
        "promedio_registros": promedio_registros
    }


def obtener_tablas_actuales():
    """Obtiene las tablas actuales en la base de datos"""
    if cursor is None:
        return []
    
    try:
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        return [list(t.values())[0] for t in tablas]
    except:
        return []


def ejecutar_respaldo_prueba():
    """Ejecuta un respaldo de prueba para verificar configuración.

    Genera los 3 archivos (Excel, PDF, SQL) y retorna las rutas para enviarlos por correo.
    """
    from services.backup_service import generar_excel, generar_pdf, generar_sql

    try:
        print("Iniciando respaldo de prueba...")
        
        tablas = obtener_todas_tablas()
        if not tablas:
            return False, "No se encontraron tablas para respaldar", [], 0, {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tipo_respaldo = "prueba"
        
        total_registros = sum(len(datos) for datos in tablas.values())
        tablas_respaldadas = {nombre: len(datos) for nombre, datos in tablas.items()}

        archivos_generados = []
        archivos_paths = []
        
        # Generar Excel de prueba
        archivo_excel = generar_excel(tablas, tipo_respaldo)
        filename_xlsx = f"backup_prueba_{timestamp}.xlsx"
        filepath_xlsx = os.path.join(BACKUPS_STORAGE_DIR, filename_xlsx)
        
        with open(filepath_xlsx, 'wb') as f:
            f.write(archivo_excel.getvalue())
        
        archivos_generados.append(filename_xlsx)
        archivos_paths.append(filepath_xlsx)

        # Generar PDF de prueba
        archivo_pdf = generar_pdf(tablas, tipo_respaldo)
        filename_pdf = f"backup_prueba_{timestamp}.pdf"
        filepath_pdf = os.path.join(BACKUPS_STORAGE_DIR, filename_pdf)
        
        with open(filepath_pdf, 'wb') as f:
            f.write(archivo_pdf.getvalue())
        
        archivos_generados.append(filename_pdf)
        archivos_paths.append(filepath_pdf)

        # Generar SQL de prueba
        archivo_sql = generar_sql(tablas, tipo_respaldo)
        filename_sql = f"backup_prueba_{timestamp}.sql"
        filepath_sql = os.path.join(BACKUPS_STORAGE_DIR, filename_sql)
        
        with open(filepath_sql, 'wb') as f:
            f.write(archivo_sql.getvalue())
        
        archivos_generados.append(filename_sql)
        archivos_paths.append(filepath_sql)

        return True, f"Respaldo de prueba exitoso: {total_registros} registros", archivos_paths, total_registros, tablas_respaldadas
    
    except Exception as e:
        return False, f"Error en respaldo de prueba: {str(e)}", [], 0, {}