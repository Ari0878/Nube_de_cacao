import os
import json
import re
from datetime import datetime
from io import BytesIO
import openpyxl
import mysql.connector
import db

RESTORE_DIR = "restore_temp"
if not os.path.exists(RESTORE_DIR):
    os.makedirs(RESTORE_DIR)

HISTORIAL_RESTORE_FILE = os.path.join(RESTORE_DIR, "historial_restauraciones.json")


# =========================
# HISTORIAL
# =========================
def cargar_historial_restauraciones():
    if os.path.exists(HISTORIAL_RESTORE_FILE):
        with open(HISTORIAL_RESTORE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def guardar_historial_restauraciones(historial):
    with open(HISTORIAL_RESTORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def agregar_historial_restauracion(tipo_archivo, tablas, registros, estado="exitoso", error=None):
    historial = cargar_historial_restauraciones()

    historial.insert(0, {
        "fecha": datetime.now().isoformat(),
        "tipo_archivo": tipo_archivo,
        "tablas": tablas,
        "registros_totales": registros,
        "estado": estado,
        "error": error
    })

    if len(historial) > 50:
        historial = historial[:50]

    guardar_historial_restauraciones(historial)


# =========================
# VALIDACIÓN
# =========================
def validar_archivo_restauracion(filename):
    ext = os.path.splitext(filename)[1].lower()
    permitidas = {'.sql', '.xlsx', '.json'}

    if ext not in permitidas:
        return False, ext, "Formato no permitido"

    return True, ext, "OK"


# =========================
# 🔥 SQL PRO
# =========================
def restaurar_desde_sql(file_content):
    try:
        conexion = db.get_connection()
        if conexion is None:
            return False, "No hay conexión", {}

        print("📄 Restaurando SQL (modo pro)...")

        sql_content = file_content.decode('utf-8')

        # 🔥 IMPORTANTE: usar conexión directa, no cursor global
        cursor_local = conexion.cursor()

        # Asegurar la base de datos existe y estamos en contexto
        cursor_local.execute("CREATE DATABASE IF NOT EXISTS `cafeteria_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        cursor_local.execute("USE `cafeteria_db`")

        # 🔥 Intentamos ejecutar en modo multi si está soportado, si no fallback.
        try:
            for result in cursor_local.execute(sql_content, multi=True):
                pass
        except TypeError:
            # El cursor no admite multi, ejecutamos cada comando separado
            script = []
            for line in sql_content.splitlines():
                line = line.strip()
                if not line or line.startswith('--') or line.startswith('#'):
                    continue
                script.append(line)

            cleaned = ' '.join(script)
            statements = [s.strip() for s in cleaned.split(';') if s.strip()]

            for statement in statements:
                cursor_local.execute(statement)

        # Calcular estadísticas reales de tablas restauradas
        tablas_res = []
        registros_res = 0
        try:
            cursor_local.execute("SHOW TABLES")
            tablas = cursor_local.fetchall() or []
            for tabla_item in tablas:
                nombre_tabla = list(tabla_item.values())[0] if isinstance(tabla_item, dict) else tabla_item[0]
                tablas_res.append(nombre_tabla)
                cursor_local.execute(f"SELECT COUNT(*) as cnt FROM `{nombre_tabla}`")
                cnt_row = cursor_local.fetchone()
                cnt = cnt_row.get("cnt") if isinstance(cnt_row, dict) else cnt_row[0]
                registros_res += cnt or 0
        except Exception:
            pass

        conexion.commit()

        print("✅ Restauración COMPLETA")

        return True, "Restauración exitosa", {"tablas": tablas_res, "total_registros": registros_res}

    except Exception as e:
        print(f"❌ ERROR RESTORE: {e}")

        try:
            conexion.rollback()
        except:
            pass

        return False, str(e), {}
# =========================
# EXCEL
# =========================
def restaurar_desde_excel(file_content):
    try:
        cursor = db.get_cursor()
        if cursor is None:
            return False, "No hay conexión", {}

        wb = openpyxl.load_workbook(BytesIO(file_content))

        total_registros = 0
        tablas_res = []

        for sheet in wb.sheetnames:
            ws = wb[sheet]
            headers = [c.value for c in ws[1] if c.value]

            if not headers:
                continue

            cols = ", ".join([f"`{h}` TEXT" for h in headers])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{sheet}` ({cols})")

            registros_tabla = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue

                placeholders = ", ".join(["%s"] * len(headers))
                cursor.execute(
                    f"INSERT INTO `{sheet}` ({', '.join(headers)}) VALUES ({placeholders})",
                    row
                )
                registros_tabla += 1

            if registros_tabla > 0:
                tablas_res.append(sheet)
                total_registros += registros_tabla

        db.get_connection().commit()
        return True, "Excel restaurado", {"tablas": tablas_res, "total_registros": total_registros}

    except Exception as e:
        if db.get_connection() is not None:
            db.get_connection().rollback()
        return False, str(e), {}


# =========================
# JSON
# =========================
def restaurar_desde_json(file_content):
    try:
        cursor = db.get_cursor()
        if cursor is None:
            return False, "No hay conexión", {}

        data = json.loads(file_content.decode('utf-8'))

        total_registros = 0
        tablas_res = []

        for table, rows in data.get("tablas", {}).items():
            if not rows:
                continue

            cols = list(rows[0].keys())
            col_sql = ", ".join([f"`{c}` TEXT" for c in cols])

            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{table}` ({col_sql})")

            registros_tabla = 0
            for r in rows:
                vals = [r.get(c) for c in cols]
                placeholders = ", ".join(["%s"] * len(cols))
                cursor.execute(
                    f"INSERT INTO `{table}` ({', '.join(cols)}) VALUES ({placeholders})",
                    vals
                )
                registros_tabla += 1

            if registros_tabla > 0:
                tablas_res.append(table)
                total_registros += registros_tabla

        db.get_connection().commit()
        return True, "JSON restaurado", {"tablas": tablas_res, "total_registros": total_registros}

    except Exception as e:
        if db.get_connection() is not None:
            db.get_connection().rollback()
        return False, str(e), {}

def obtener_estadisticas_restauraciones():
    """Obtiene estadísticas del historial de restauraciones"""
    historial = cargar_historial_restauraciones()

    if not historial:
        return {
            "total_restauraciones": 0,
            "exitosas": 0,
            "fallidas": 0,
            "ultima_restauracion": None,
            "total_registros_restaurados": 0
        }

    exitosas = sum(1 for h in historial if h.get("estado") == "exitoso")
    fallidas = len(historial) - exitosas
    total_registros = sum(
        h.get("registros_totales", 0)
        for h in historial
        if h.get("estado") == "exitoso"
    )

    return {
        "total_restauraciones": len(historial),
        "exitosas": exitosas,
        "fallidas": fallidas,
        "ultima_restauracion": historial[0].get("fecha"),
        "total_registros_restaurados": total_registros
    }