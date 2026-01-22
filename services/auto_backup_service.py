# services/auto_backup_service.py

import os
import json
import shutil
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import db

# Directorio para configuración de respaldos automáticos
AUTO_BACKUP_DIR = "auto_backup_config"
BACKUPS_STORAGE_DIR = "backups_automaticos"  # Carpeta donde se guardarán los archivos

# Crear directorios si no existen
for directory in [AUTO_BACKUP_DIR, BACKUPS_STORAGE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

CONFIG_FILE = os.path.join(AUTO_BACKUP_DIR, "config.json")
HISTORIAL_FILE = os.path.join(AUTO_BACKUP_DIR, "historial.json")

# Scheduler global
scheduler = BackgroundScheduler()
scheduler.start()


def cargar_config():
    """Carga la configuración de respaldos automáticos"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Configuración por defecto
    return {
        "activo": False,
        "hora": "02:00",
        "frecuencia": "diario",  # diario, semanal, mensual
        "dia_semana": "monday",  # para semanal
        "dia_mes": 1,  # para mensual
        "formato": "todos",  # todos, excel, pdf, sql
        "limpiar_antiguos": True,
        "dias_retener": 30
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


def agregar_historial(formato, cantidad_registros, archivos_generados=None, estado="exitoso"):
    """Agrega una entrada al historial"""
    historial = cargar_historial()
    
    entrada = {
        "fecha": datetime.now().isoformat(),
        "formato": formato,
        "cantidad_registros": cantidad_registros,
        "archivos": archivos_generados or [],
        "estado": estado
    }
    
    historial.insert(0, entrada)  # Agregar al inicio
    
    # Mantener solo los últimos 100 registros
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
    
    if config["frecuencia"] == "diario":
        # Próximos 5 días
        for i in range(5):
            fecha = ahora + timedelta(days=i)
            fecha = fecha.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if fecha > ahora:
                proximos.append({
                    "tarea": f"Respaldo Diario ({config['formato'].upper()})",
                    "proxima_ejecucion": fecha.strftime("%Y-%m-%d %H:%M")
                })
            
            if len(proximos) >= 5:
                break
    
    elif config["frecuencia"] == "semanal":
        # Mapeo de días
        dias_semana = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        dia_objetivo = dias_semana.get(config.get("dia_semana", "monday"), 0)
        
        # Próximas 5 semanas
        for i in range(10):
            dias_hasta = (dia_objetivo - ahora.weekday() + 7 * i) % 7
            if dias_hasta == 0 and i == 0:
                dias_hasta = 7
            
            fecha = ahora + timedelta(days=dias_hasta)
            fecha = fecha.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if fecha > ahora:
                proximos.append({
                    "tarea": f"Respaldo Semanal ({config['formato'].upper()})",
                    "proxima_ejecucion": fecha.strftime("%Y-%m-%d %H:%M")
                })
            
            if len(proximos) >= 5:
                break
    
    elif config["frecuencia"] == "mensual":
        dia_mes = config.get("dia_mes", 1)
        
        # Próximos 5 meses
        for i in range(12):
            try:
                mes = ahora.month + i
                año = ahora.year + (mes - 1) // 12
                mes = ((mes - 1) % 12) + 1
                
                fecha = datetime(año, mes, min(dia_mes, 28), hour, minute)
                
                if fecha > ahora:
                    proximos.append({
                        "tarea": f"Respaldo Mensual ({config['formato'].upper()})",
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
    Genera archivos y los guarda en la carpeta backups_automaticos/
    """
    from services.backup_service import (
        generar_backup_completo,
        generar_excel,
        generar_pdf,
        generar_sql
    )
    
    config = cargar_config()
    
    if not config.get("activo"):
        return
    
    try:
        print(f"🔄 Iniciando respaldo automático...")
        
        # Generar respaldo completo
        ventas, cantidad = generar_backup_completo()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        formato_config = config.get("formato", "todos")
        
        archivos_generados = []
        
        # Generar archivos según configuración
        if formato_config == "todos" or formato_config == "excel":
            archivo_excel = generar_excel(ventas, "automatico")
            filename = f"backup_auto_{timestamp}.xlsx"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_excel.getvalue())
            
            archivos_generados.append(filename)
            print(f"  ✅ Excel generado: {filename}")
        
        if formato_config == "todos" or formato_config == "pdf":
            archivo_pdf = generar_pdf(ventas, "automatico")
            filename = f"backup_auto_{timestamp}.pdf"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_pdf.getvalue())
            
            archivos_generados.append(filename)
            print(f"  ✅ PDF generado: {filename}")
        
        if formato_config == "todos" or formato_config == "sql":
            archivo_sql = generar_sql(ventas, "automatico")
            filename = f"backup_auto_{timestamp}.sql"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_sql.getvalue())
            
            archivos_generados.append(filename)
            print(f"  ✅ SQL generado: {filename}")
        
        # Registrar en historial
        agregar_historial(formato_config, cantidad, archivos_generados, "exitoso")
        
        print(f"✅ Respaldo automático completado: {cantidad} registros, {len(archivos_generados)} archivo(s)")
        
        # Limpiar archivos antiguos si está configurado
        if config.get("limpiar_antiguos", False):
            limpiar_backups_antiguos(config.get("dias_retener", 30))
        
    except Exception as e:
        print(f"❌ Error en respaldo automático: {e}")
        agregar_historial("error", 0, [], f"error: {str(e)}")


def limpiar_backups_antiguos(dias_retener=30):
    """
    Elimina archivos de respaldo más antiguos que el número de días especificado
    """
    try:
        ahora = datetime.now()
        limite = ahora - timedelta(days=dias_retener)
        
        archivos_eliminados = 0
        
        for filename in os.listdir(BACKUPS_STORAGE_DIR):
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            if os.path.isfile(filepath):
                # Obtener fecha de modificación del archivo
                fecha_modificacion = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if fecha_modificacion < limite:
                    os.remove(filepath)
                    archivos_eliminados += 1
                    print(f"  🗑️ Eliminado: {filename}")
        
        if archivos_eliminados > 0:
            print(f"🧹 Limpieza completada: {archivos_eliminados} archivo(s) eliminado(s)")
        
    except Exception as e:
        print(f"⚠️ Error al limpiar archivos antiguos: {e}")


def listar_archivos_guardados():
    """
    Lista todos los archivos de respaldo guardados con su información
    """
    archivos = []
    ahora = datetime.now()
    
    try:
        for filename in os.listdir(BACKUPS_STORAGE_DIR):
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                fecha_mod = datetime.fromtimestamp(stat.st_mtime)
                
                # Detectar si es nuevo (menos de 1 hora)
                es_nuevo = (ahora - fecha_mod).seconds < 3600
                
                # Detectar tipo de respaldo
                if 'manual' in filename:
                    tipo_respaldo = "Manual"
                    tipo_color = "info"
                elif 'auto' in filename:
                    tipo_respaldo = "Automático"
                    tipo_color = "success"
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
        
        # Ordenar por fecha (más recientes primero)
        archivos.sort(key=lambda x: x["fecha"], reverse=True)
        
    except Exception as e:
        print(f"Error al listar archivos: {e}")
    
    return archivos


def eliminar_archivo(filename):
    """
    Elimina un archivo de respaldo específico
    """
    try:
        filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, "Archivo eliminado exitosamente"
        else:
            return False, "Archivo no encontrado"
    
    except Exception as e:
        return False, f"Error al eliminar archivo: {str(e)}"


def obtener_estadisticas_storage():
    """
    Obtiene estadísticas del almacenamiento de respaldos
    """
    try:
        archivos = listar_archivos_guardados()
        
        total_archivos = len(archivos)
        tamaño_total = sum(a["tamaño"] for a in archivos)
        tamaño_total_mb = round(tamaño_total / (1024 * 1024), 2)
        
        # Contar por tipo
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
        print(f"Error al obtener estadísticas: {e}")
        return {
            "total_archivos": 0,
            "tamaño_total_mb": 0,
            "por_tipo": {},
            "ultimo_respaldo": None
        }


def configurar_scheduler():
    """Configura el scheduler según la configuración guardada"""
    config = cargar_config()
    
    # Limpiar trabajos existentes
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
    
    # Configurar trigger según frecuencia
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
        # Mapeo de días
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
            "total_registros": 0
        }
    
    exitosos = sum(1 for h in historial if h.get("estado") == "exitoso" or h.get("estado") == "manual")
    fallidos = len(historial) - exitosos
    total_registros = sum(h.get("cantidad_registros", 0) for h in historial if "exitoso" in h.get("estado", ""))
    
    return {
        "total_respaldos": len(historial),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "ultimo_respaldo": historial[0].get("fecha") if historial else None,
        "total_registros": total_registros
    }


# Inicializar scheduler al importar el módulo
configurar_scheduler()