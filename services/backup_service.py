# services/backup_service.py
import os
import json
from datetime import datetime
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import db

BACKUP_DIR = "backups_metadata"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

METADATA_FILE = os.path.join(BACKUP_DIR, "backup_metadata.json")


# =========================
# METADATA
# =========================
def cargar_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "ultimo_completo": None,
        "ultimo_incremental": None,
        "ultimo_diferencial": None,
        "tablas_respaldadas": {}
    }


def guardar_metadata(metadata):
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


# =========================
# 🔥 OBTENER TABLAS (FIX PRINCIPAL)
# =========================
def obtener_todas_tablas():
    tablas = {}

    if db.get_cursor() is None:
        print("❌ No hay conexión a la BD")
        return tablas

    try:
        cursor = db.get_cursor()
        cursor.execute("SHOW TABLES")
        tablas_nombres = cursor.fetchall()

        for tabla_item in tablas_nombres:
            # 🔥 FIX: compatible con tuplas o dict
            if isinstance(tabla_item, dict):
                nombre_tabla = list(tabla_item.values())[0]
            else:
                nombre_tabla = tabla_item[0]

            cursor.execute(f"SELECT * FROM `{nombre_tabla}`")
            filas = cursor.fetchall()

            datos_tabla = []

            # 🔥 convertir a dict siempre
            if filas:
                if isinstance(filas[0], dict):
                    datos_tabla = filas
                else:
                    columnas = [desc[0] for desc in cursor.description]
                    for fila in filas:
                        fila_dict = {}
                        for i, value in enumerate(fila):
                            if isinstance(value, datetime):
                                fila_dict[columnas[i]] = value.isoformat()
                            else:
                                fila_dict[columnas[i]] = value
                        datos_tabla.append(fila_dict)

            tablas[nombre_tabla] = datos_tabla

    except Exception as e:
        print(f"❌ Error al obtener tablas: {e}")

    return tablas


# =========================
# BACKUPS
# =========================
def generar_backup_completo():
    tablas = obtener_todas_tablas()

    metadata = cargar_metadata()
    metadata["ultimo_completo"] = datetime.now().isoformat()
    metadata["tablas_respaldadas"] = {
        nombre: len(datos) for nombre, datos in tablas.items()
    }

    guardar_metadata(metadata)

    total = sum(len(d) for d in tablas.values())
    return tablas, total


def generar_backup_incremental():
    tablas = obtener_todas_tablas()

    metadata = cargar_metadata()
    metadata["ultimo_incremental"] = datetime.now().isoformat()
    guardar_metadata(metadata)

    total = sum(len(d) for d in tablas.values())
    return tablas, total


def generar_backup_diferencial():
    tablas = obtener_todas_tablas()

    metadata = cargar_metadata()
    metadata["ultimo_diferencial"] = datetime.now().isoformat()
    guardar_metadata(metadata)

    total = sum(len(d) for d in tablas.values())
    return tablas, total


# =========================
# EXCEL
# =========================
def generar_excel(tablas, tipo_respaldo="completo"):
    try:
        wb = Workbook()
        wb.remove(wb.active)

        info_ws = wb.create_sheet("📊 Información", 0)
        info_ws['A1'] = "🌐 Nube de Cacao - Respaldo"
        info_ws['A3'] = f"Fecha: {datetime.now()}"
        info_ws['A4'] = f"Tipo: {tipo_respaldo}"

        for nombre_tabla, datos in tablas.items():
            if not datos:
                continue

            ws = wb.create_sheet(nombre_tabla[:31])
            columnas = list(datos[0].keys())

            for col_idx, col in enumerate(columnas, 1):
                ws.cell(row=1, column=col_idx, value=col)

            for row_idx, fila in enumerate(datos, 2):
                for col_idx, col in enumerate(columnas, 1):
                    ws.cell(row=row_idx, column=col_idx, value=str(fila.get(col)))

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer

    except Exception as e:
        print(f"❌ Error Excel: {e}")
        return BytesIO()

def generar_pdf(tablas, tipo_backup):
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from io import BytesIO

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    elementos = []

    styles = getSampleStyleSheet()

    # Título
    elementos.append(Paragraph(f"Backup {tipo_backup.upper()}", styles['Title']))
    elementos.append(Spacer(1, 20))

    # Resumen
    total_registros = sum(len(datos) for datos in tablas.values())

    info = [
        ["Fecha", str(datetime.now())],
        ["Tipo", tipo_backup],
        ["Tablas", str(len(tablas))],
        ["Registros", str(total_registros)]
    ]

    tabla_info = Table(info)
    tabla_info.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))

    elementos.append(tabla_info)
    elementos.append(Spacer(1, 20))

    # Tablas
    for nombre, datos in tablas.items():
        elementos.append(Paragraph(f"Tabla: {nombre}", styles['Heading2']))

        if datos:
            columnas = list(datos[0].keys())
            data = [columnas]

            for fila in datos[:10]:  # solo muestra 10
                data.append([str(fila.get(c, "")) for c in columnas])

            tabla = Table(data)
            tabla.setStyle(TableStyle([
                ("GRID", (0,0), (-1,-1), 1, colors.black)
            ]))

            elementos.append(tabla)

        elementos.append(Spacer(1, 20))

    doc.build(elementos)
    output.seek(0)

    return output

# =========================
# 🔥 SQL (MEJORADO)
# =========================
def generar_sql(tablas, tipo_backup):
    try:
        output = BytesIO()

        total_tablas = len(tablas)
        sql = f"""-- ============================================
-- Backup {tipo_backup.upper()}
-- Fecha: {datetime.now()}
-- ============================================

CREATE DATABASE IF NOT EXISTS `cafeteria_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `cafeteria_db`;

-- Tablas a respaldar: {total_tablas}
"""

        if total_tablas == 0:
            sql += "-- No se encontraron tablas en la base de datos.\n"

        sql += "\nSET FOREIGN_KEY_CHECKS=0;\n\n"

        cursor = db.get_cursor()
        for tabla in tablas.keys():

            # 🔥 OBTENER ESTRUCTURA REAL
            cursor.execute(f"SHOW CREATE TABLE `{tabla}`")
            result = cursor.fetchone()

            if isinstance(result, dict):
                create_stmt = list(result.values())[1]
            else:
                create_stmt = result[1]

            sql += f"\n-- Estructura de {tabla}\n"
            sql += f"DROP TABLE IF EXISTS `{tabla}`;\n"
            sql += create_stmt + ";\n\n"

            filas = tablas[tabla]

            if not filas:
                continue

            sql += f"-- Datos de {tabla}\n"

            for fila in filas:
                columnas = ", ".join(f"`{k}`" for k in fila.keys())

                valores = []
                for v in fila.values():
                    if v is None:
                        valores.append("NULL")
                    elif isinstance(v, (int, float)):
                        valores.append(str(v))
                    else:
                        v = str(v).replace("'", "''")
                        valores.append(f"'{v}'")

                valores_str = ", ".join(valores)

                sql += f"INSERT INTO `{tabla}` ({columnas}) VALUES ({valores_str});\n"

        sql += "\nSET FOREIGN_KEY_CHECKS=1;"

        output.write(sql.encode('utf-8'))
        output.seek(0)

        print("🔥 Backup SQL COMPLETO generado")
        return output

    except Exception as e:
        print(f"❌ Error SQL: {e}")
        return BytesIO()

# =========================
# INFO RESPALDOS (FIX)
# =========================
def obtener_info_respaldos():
    metadata = cargar_metadata()

    nombres_tablas = []

    try:
        cursor = db.get_cursor()
        if cursor is None:
            return {
                "ultimo_completo": metadata.get("ultimo_completo"),
                "ultimo_incremental": metadata.get("ultimo_incremental"),
                "ultimo_diferencial": metadata.get("ultimo_diferencial"),
                "tablas_actuales": nombres_tablas,
                "tablas_respaldadas": metadata.get("tablas_respaldadas", {})
            }

        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()

        for t in tablas:
            if isinstance(t, dict):
                nombres_tablas.append(list(t.values())[0])
            else:
                nombres_tablas.append(t[0])

    except Exception as e:
        print(f"❌ Error tablas actuales: {e}")

    return {
        "ultimo_completo": metadata.get("ultimo_completo"),
        "ultimo_incremental": metadata.get("ultimo_incremental"),
        "ultimo_diferencial": metadata.get("ultimo_diferencial"),
        "tablas_actuales": nombres_tablas,
        "tablas_respaldadas": metadata.get("tablas_respaldadas", {})
    }