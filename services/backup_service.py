import os
import json
from datetime import datetime
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
# Corregir importación de PageSetup
from openpyxl.worksheet.page import PageMargins
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch, cm
from db import db, collection, usuarios_col
import pickle


# Directorio para almacenar metadatos de respaldos
BACKUP_DIR = "backups_metadata"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

METADATA_FILE = os.path.join(BACKUP_DIR, "backup_metadata.json")


def cargar_metadata():
    """Carga el metadata de respaldos anteriores"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "ultimo_completo": None,
        "ultimo_incremental": None,
        "ultimo_diferencial": None,
        "colecciones_respaldadas": {}
    }


def guardar_metadata(metadata):
    """Guarda el metadata de respaldos"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, ensure_ascii=False, indent=2, fp=f)


def obtener_todas_colecciones():
    """
    Obtiene todas las colecciones de la base de datos
    Retorna: diccionario con {nombre_coleccion: datos}
    """
    colecciones = {}
    
    # Verificar si la conexión a la base de datos está disponible
    if db is None:
        print("Error: No hay conexión a la base de datos")
        return colecciones
    
    try:
        # Listar todas las colecciones en la base de datos
        nombres_colecciones = db.list_collection_names()
        
        for nombre in nombres_colecciones:
            # Saltar colecciones del sistema
            if nombre.startswith('system.'):
                continue
                
            coleccion = db[nombre]
            datos = list(coleccion.find({}))
            
            # Convertir ObjectId a string y fechas a ISO
            for documento in datos:
                documento["_id"] = str(documento["_id"])
                for key, value in documento.items():
                    if isinstance(value, datetime):
                        documento[key] = value.isoformat()
            
            colecciones[nombre] = datos
    
    except Exception as e:
        print(f"Error al obtener colecciones: {e}")
    
    return colecciones


def generar_backup_completo():
    """
    Genera un respaldo completo de toda la base de datos
    Retorna: (datos_colecciones, metadata_actualizado)
    """
    colecciones = obtener_todas_colecciones()
    
    # Actualizar metadata
    metadata = cargar_metadata()
    metadata["ultimo_completo"] = datetime.now().isoformat()
    
    # Guardar información de qué colecciones se respaldaron
    metadata["colecciones_respaldadas"] = {
        nombre: len(datos) for nombre, datos in colecciones.items()
    }
    
    guardar_metadata(metadata)
    
    total_registros = sum(len(datos) for datos in colecciones.values())
    return colecciones, total_registros


def generar_backup_incremental():
    """
    Genera un respaldo incremental (solo registros nuevos desde el último respaldo)
    Retorna: (datos_colecciones, cantidad_total)
    """
    metadata = cargar_metadata()
    
    # Si no hay respaldo previo, hacer completo
    if not metadata.get("ultimo_incremental") and not metadata.get("ultimo_completo"):
        return generar_backup_completo()
    
    # Verificar si la conexión a la base de datos está disponible
    if db is None:
        print("Error: No hay conexión a la base de datos")
        return {}, 0
    
    # Obtener la fecha del último respaldo
    ultimo_respaldo = metadata.get("ultimo_incremental") or metadata.get("ultimo_completo")
    fecha_ultimo = datetime.fromisoformat(ultimo_respaldo)
    
    # Obtener todas las colecciones
    try:
        nombres_colecciones = db.list_collection_names()
    except:
        return {}, 0
    
    colecciones_nuevas = {}
    
    for nombre in nombres_colecciones:
        if nombre.startswith('system.'):
            continue
            
        coleccion = db[nombre]
        
        # Intentar filtrar por fecha de creación (si existe el campo)
        try:
            # Buscar documentos creados después del último respaldo
            documentos_nuevos = list(coleccion.find({"created_at": {"$gt": fecha_ultimo}}))
            
            # Si no hay campo created_at, obtener todos
            if not documentos_nuevos:
                documentos_nuevos = list(coleccion.find({}))
        except:
            # Si hay error, obtener todos
            documentos_nuevos = list(coleccion.find({}))
        
        # Convertir ObjectId a string y fechas a ISO
        for documento in documentos_nuevos:
            documento["_id"] = str(documento["_id"])
            for key, value in documento.items():
                if isinstance(value, datetime):
                    documento[key] = value.isoformat()
        
        colecciones_nuevas[nombre] = documentos_nuevos
    
    # Actualizar metadata
    metadata["ultimo_incremental"] = datetime.now().isoformat()
    guardar_metadata(metadata)
    
    total_registros = sum(len(datos) for datos in colecciones_nuevas.values())
    return colecciones_nuevas, total_registros


def generar_backup_diferencial():
    """
    Genera un respaldo diferencial (cambios desde el último respaldo completo)
    Retorna: (datos_colecciones, cantidad)
    """
    metadata = cargar_metadata()
    
    # Si no hay respaldo completo, hacer uno
    if not metadata.get("ultimo_completo"):
        return generar_backup_completo()
    
    # Verificar si la conexión a la base de datos está disponible
    if db is None:
        print("Error: No hay conexión a la base de datos")
        return {}, 0
    
    fecha_completo = datetime.fromisoformat(metadata["ultimo_completo"])
    
    # Obtener todas las colecciones
    try:
        nombres_colecciones = db.list_collection_names()
    except:
        return {}, 0
    
    colecciones_diferenciales = {}
    
    for nombre in nombres_colecciones:
        if nombre.startswith('system.'):
            continue
            
        coleccion = db[nombre]
        
        # Buscar documentos modificados después del último completo
        try:
            documentos = list(coleccion.find({
                "$or": [
                    {"created_at": {"$gt": fecha_completo}},
                    {"updated_at": {"$gt": fecha_completo}}
                ]
            }))
            
            if not documentos:
                documentos = list(coleccion.find({}))
        except:
            documentos = list(coleccion.find({}))
        
        # Convertir ObjectId a string y fechas a ISO
        for documento in documentos:
            documento["_id"] = str(documento["_id"])
            for key, value in documento.items():
                if isinstance(value, datetime):
                    documento[key] = value.isoformat()
        
        colecciones_diferenciales[nombre] = documentos
    
    # Actualizar metadata
    metadata["ultimo_diferencial"] = datetime.now().isoformat()
    guardar_metadata(metadata)
    
    total_registros = sum(len(datos) for datos in colecciones_diferenciales.values())
    return colecciones_diferenciales, total_registros


def auto_ajustar_ancho_columnas(worksheet):
    """
    Ajusta automáticamente el ancho de las columnas en una hoja de Excel
    """
    for column in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                if cell.value:
                    # Calcular longitud del contenido
                    cell_length = len(str(cell.value))
                    
                    # Ajustar si hay saltos de línea
                    if '\n' in str(cell.value):
                        lines = str(cell.value).split('\n')
                        cell_length = max(len(line) for line in lines)
                    
                    if cell_length > max_length:
                        max_length = cell_length
            except:
                pass
        
        # Limitar el ancho máximo a 50
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width


def configurar_pagina_horizontal(worksheet):
    """
    Configura una hoja de Excel para orientación horizontal
    """
    # Configurar orientación horizontal
    worksheet.page_setup.orientation = worksheet.ORIENTATION_LANDSCAPE
    worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4
    
    # Configurar márgenes
    worksheet.page_margins = PageMargins(
        left=0.25, right=0.25,
        top=0.75, bottom=0.75,
        header=0.3, footer=0.3
    )


def generar_excel(colecciones, tipo_respaldo="completo"):
    """
    Genera un archivo Excel con todas las colecciones
    """
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from datetime import datetime
    import json
    
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remover hoja por defecto
    
    for nombre_coleccion, datos in colecciones.items():
        if not datos:
            continue
        
        ws = wb.create_sheet(nombre_coleccion[:31])  # Excel limita a 31 caracteres
        
        # Obtener todas las claves únicas
        todas_claves = set()
        for doc in datos:
            todas_claves.update(doc.keys())
        
        claves = sorted(todas_claves)
        
        # Encabezados
        header_fill = PatternFill(start_color="DAA520", end_color="DAA520", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col_idx, clave in enumerate(claves, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = clave
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # Datos
        for row_idx, doc in enumerate(datos, 2):
            for col_idx, clave in enumerate(claves, 1):
                valor = doc.get(clave, "")
                
                # Convertir valores complejos a string JSON
                if isinstance(valor, (dict, list)):
                    valor = json.dumps(valor, ensure_ascii=False)
                elif isinstance(valor, datetime):
                    valor = valor.strftime("%Y-%m-%d %H:%M:%S")
                elif valor is None:
                    valor = ""
                
                ws.cell(row=row_idx, column=col_idx, value=str(valor))
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Agregar hoja de información
    info_ws = wb.create_sheet("Información", 0)
    info_ws['A1'] = "Nube de Cacao - Respaldo de Base de Datos"
    info_ws['A1'].font = Font(size=16, bold=True)
    info_ws['A3'] = f"Fecha de Respaldo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    info_ws['A4'] = f"Tipo de Respaldo: {tipo_respaldo.upper()}"
    info_ws['A5'] = f"Total de Colecciones: {len(colecciones)}"
    info_ws['A6'] = f"Total de Registros: {sum(len(d) for d in colecciones.values())}"
    
    # Guardar en memoria
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer

def generar_pdf(colecciones, tipo_backup):
    """
    Genera un archivo PDF con resumen de todas las colecciones en formato horizontal
    Retorna: BytesIO con el contenido del PDF
    """
    output = BytesIO()
    
    # Usar tamaño de página horizontal (landscape)
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    titulo_style = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#4A2C2A'),
        spaceAfter=40,
        alignment=1,  # Centrado
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4A2C2A'),
        spaceAfter=20,
        spaceBefore=30,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal con wrap
    texto_wrap_style = ParagraphStyle(
        'TextoWrap',
        parent=styles['Normal'],
        fontSize=9,
        wordWrap='CJK',  # Permite wrap de texto largo
        spaceAfter=6
    )
    
    # Estilo para encabezados de tabla
    encabezado_style = ParagraphStyle(
        'EncabezadoTabla',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    # Título principal
    titulo = Paragraph(f"RESPALDO COMPLETO DE BASE DE DATOS - {tipo_backup.upper()}", titulo_style)
    elementos.append(titulo)
    
    # Información del respaldo
    elementos.append(Paragraph("INFORMACIÓN DEL RESPALDO", subtitulo_style))
    
    total_registros = sum(len(datos) for datos in colecciones.values())
    info_data = [
        ['Fecha de Generación:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ['Tipo de Respaldo:', tipo_backup.upper()],
        ['Base de Datos:', 'cafeteria_db'],
        ['Total de Colecciones:', str(len(colecciones))],
        ['Total de Registros:', str(total_registros)],
        ['Sistema:', 'Nube de Cacao - Sistema de Ventas']
    ]
    
    info_table = Table(info_data, colWidths=[3*inch, 5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5E6D3')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4A2C2A')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#8B4513')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elementos.append(info_table)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Resumen por colección
    elementos.append(Paragraph("RESUMEN POR COLECCIÓN", subtitulo_style))
    
    resumen_data = [['Colección', 'Registros', 'Muestra']]
    
    for nombre, datos in colecciones.items():
        cantidad = len(datos)
        muestra = "No hay registros"
        
        if cantidad > 0:
            if cantidad <= 5:
                muestra = f"{cantidad} registros"
            else:
                muestra = f"{cantidad} registros (primeros 5 en PDF)"
        
        resumen_data.append([nombre, str(cantidad), muestra])
    
    # Calcular ancho de columnas para aprovechar espacio horizontal
    ancho_total = landscape(letter)[0] - 2*inch  # Ancho disponible
    anchos_columnas = [ancho_total * 0.4, ancho_total * 0.2, ancho_total * 0.4]
    
    resumen_table = Table(resumen_data, colWidths=anchos_columnas)
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A2C2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF8DC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFF8DC'), colors.HexColor('#F5E6D3')]),
    ]))
    
    elementos.append(resumen_table)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Datos de cada colección (limitado)
    for idx, (nombre, datos) in enumerate(colecciones.items()):
        if datos:
            # Agregar salto de página si no es la primera colección y hay muchos datos
            if idx > 0 and len(datos) > 20:
                elementos.append(PageBreak())
                elementos.append(Paragraph(f"COLECCIÓN: {nombre.upper()}", subtitulo_style))
            else:
                elementos.append(Paragraph(f"COLECCIÓN: {nombre.upper()}", subtitulo_style))
            
            # Limitar a 15 registros por colección para evitar PDFs muy grandes
            datos_limitados = datos[:15]
            
            if datos_limitados:
                # Obtener todas las columnas únicas de los registros
                columnas = set()
                for documento in datos_limitados:
                    columnas.update(documento.keys())
                columnas = sorted(list(columnas))
                
                # Preparar datos de tabla
                datos_tabla = []
                encabezados = []
                
                # Crear encabezados como Paragraph para permitir wrap
                for col in columnas:
                    encabezados.append(Paragraph(str(col), encabezado_style))
                datos_tabla.append(encabezados)
                
                # Agregar datos
                for documento in datos_limitados:
                    fila = []
                    for col in columnas:
                        valor = documento.get(col, 'N/A')
                        valor_str = str(valor)
                        
                        # Truncar texto muy largo
                        if len(valor_str) > 100:
                            valor_str = valor_str[:97] + "..."
                        
                        # Usar Paragraph para permitir wrap
                        fila.append(Paragraph(valor_str, texto_wrap_style))
                    datos_tabla.append(fila)
                
                # Calcular anchos de columnas dinámicamente
                num_columnas = len(columnas)
                if num_columnas > 0:
                    # Usar todo el ancho disponible
                    ancho_disponible = landscape(letter)[0] - 2*inch
                    ancho_minimo = 0.8*inch
                    ancho_maximo = 3*inch
                    
                    # Distribuir espacio equitativamente
                    ancho_columna = min(max(ancho_disponible / num_columnas, ancho_minimo), ancho_maximo)
                    anchos = [ancho_columna] * num_columnas
                    
                    # Crear tabla
                    tabla = Table(datos_tabla, colWidths=anchos, repeatRows=1)
                    
                    # Estilo de tabla
                    tabla.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B4513')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF8DC')),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
                         [colors.HexColor('#FFF8DC'), colors.HexColor('#F5E6D3')]),
                    ]))
                    
                    elementos.append(tabla)
                    
                    if len(datos) > 15:
                        nota = Paragraph(
                            f"<i>Nota: Se muestran 15 de {len(datos)} registros totales en esta colección.</i>", 
                            styles['Normal']
                        )
                        elementos.append(Spacer(1, 0.2*inch))
                        elementos.append(nota)
                    
                    elementos.append(Spacer(1, 0.4*inch))
    
    # Construir documento
    doc.build(elementos)
    output.seek(0)
    return output


def generar_json(colecciones, tipo_backup):
    """
    Genera un archivo JSON con todos los datos
    Retorna: BytesIO con el contenido JSON
    """
    datos_completos = {
        "metadata": {
            "fecha_generacion": datetime.now().isoformat(),
            "tipo_respaldo": tipo_backup,
            "base_datos": "cafeteria_db",
            "total_colecciones": len(colecciones),
            "total_registros": sum(len(datos) for datos in colecciones.values())
        },
        "colecciones": colecciones
    }
    
    output = BytesIO()
    json_str = json.dumps(datos_completos, ensure_ascii=False, indent=2)
    output.write(json_str.encode('utf-8'))
    output.seek(0)
    return output


def generar_sql(colecciones, tipo_backup):
    """
    Genera un archivo SQL con los datos de respaldo
    Retorna: BytesIO con el contenido SQL
    """
    output = BytesIO()
    
    nombres_colecciones = list(colecciones.keys()) if colecciones else []
    
    sql_content = f"""-- ============================================
-- Respaldo Completo de Base de Datos - Nube de Cacao
-- Tipo: {tipo_backup.upper()}
-- Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Base de Datos: cafeteria_db
-- Colecciones: {', '.join(nombres_colecciones)}
-- ============================================

"""
    
    for nombre_coleccion, documentos in colecciones.items():
        # Crear tabla para cada colección
        tabla_sql = nombre_coleccion.replace('.', '_')
        
        sql_content += f"""
-- -----------------------------------------------------
-- Colección: {nombre_coleccion}
-- -----------------------------------------------------

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS {tabla_sql} (
    mongo_id VARCHAR(50) PRIMARY KEY,
    datos JSON
);

-- Limpiar tabla antes de insertar (opcional)
-- TRUNCATE TABLE {tabla_sql};

"""
        
        # Insertar datos
        if documentos:
            sql_content += f"-- Insertar {len(documentos)} registros\n"
            for doc in documentos:
                # Convertir a JSON string
                datos_json = json.dumps(doc, ensure_ascii=False).replace("'", "''")
                mongo_id = doc.get('_id', '')
                
                sql_content += f"""INSERT INTO {tabla_sql} (mongo_id, datos) 
VALUES ('{mongo_id}', '{datos_json}');
"""
        else:
            sql_content += "-- No hay registros para esta colección\n"
        
        sql_content += "\n"
    
    sql_content += "-- Fin del respaldo completo\n"
    
    output.write(sql_content.encode('utf-8'))
    output.seek(0)
    return output


def obtener_info_respaldos():
    """
    Retorna información sobre los respaldos realizados
    """
    metadata = cargar_metadata()
    
    # Obtener información actual de la base de datos
    nombres_colecciones = []
    if db is not None:
        try:
            nombres_colecciones = [col for col in db.list_collection_names() 
                                  if not col.startswith('system.')]
        except Exception as e:
            print(f"Error al obtener colecciones: {e}")
            nombres_colecciones = []
    
    return {
        "ultimo_completo": metadata.get("ultimo_completo"),
        "ultimo_incremental": metadata.get("ultimo_incremental"),
        "ultimo_diferencial": metadata.get("ultimo_diferencial"),
        "colecciones_actuales": nombres_colecciones,
        "colecciones_respaldadas": metadata.get("colecciones_respaldadas", {})
    }