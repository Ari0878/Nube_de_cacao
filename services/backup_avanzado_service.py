# services/backup_avanzado_service.py
import io
import json
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from db import cursor, conn
import pandas as pd


def obtener_ultima_fecha_respaldo(tipo_respaldo):
    """
    Obtiene la fecha del último respaldo realizado de un tipo específico.
    """
    try:
        if cursor is None:
            return None
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_respaldos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo_respaldo VARCHAR(50),
                tipo_formato VARCHAR(50),
                total_registros INT,
                fecha DATETIME,
                exitoso BOOLEAN
            )
        """)
        
        cursor.execute("""
            SELECT fecha FROM historial_respaldos 
            WHERE tipo_respaldo = %s AND exitoso = TRUE 
            ORDER BY fecha DESC LIMIT 1
        """, (tipo_respaldo,))
        
        resultado = cursor.fetchone()
        
        if resultado and resultado.get("fecha"):
            return resultado["fecha"]
        return None
    except Exception as e:
        print(f"Error obteniendo última fecha: {e}")
        return None


def registrar_respaldo_realizado(tipo_respaldo, tipo_formato, total_registros):
    """Registra el respaldo en el historial"""
    try:
        if cursor is None or conn is None:
            return
        
        cursor.execute("""
            INSERT INTO historial_respaldos 
            (tipo_respaldo, tipo_formato, total_registros, fecha, exitoso)
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo_respaldo, tipo_formato, total_registros, datetime.now(), True))
        
        conn.commit()
    except Exception as e:
        print(f"Error al registrar respaldo: {e}")


def obtener_datos_completos():
    """
    Obtiene TODOS los datos de TODAS las tablas de la base de datos.
    """
    try:
        if cursor is None:
            return None, 0
        
        # Obtener todas las tablas
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        
        # Excluir tablas del sistema
        tablas_excluidas = ["historial_respaldos", "configuracion_respaldos", "respaldos_automaticos"]
        
        datos_completos = {}
        total_registros = 0
        
        for tabla_item in tablas:
            nombre_tabla = list(tabla_item.values())[0]
            
            if nombre_tabla in tablas_excluidas:
                continue
            
            try:
                cursor.execute(f"SELECT * FROM {nombre_tabla}")
                filas = cursor.fetchall()
                
                # Convertir fechas a string
                filas_procesadas = []
                for fila in filas:
                    fila_dict = {}
                    for key, value in fila.items():
                        if isinstance(value, datetime):
                            fila_dict[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            fila_dict[key] = value
                    filas_procesadas.append(fila_dict)
                
                if filas_procesadas:
                    datos_completos[nombre_tabla] = filas_procesadas
                    total_registros += len(filas_procesadas)
                    
            except Exception as e:
                print(f"Error obteniendo datos de {nombre_tabla}: {e}")
                continue
        
        return datos_completos, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos completos: {e}")
        return None, 0


def obtener_datos_incremental():
    """
    Obtiene solo los datos NUEVOS desde el último respaldo incremental.
    """
    try:
        if cursor is None:
            return None, 0
        
        ultima_fecha = obtener_ultima_fecha_respaldo("incremental")
        
        # Si no hay respaldo previo, hacer completo
        if ultima_fecha is None:
            return obtener_datos_completos()
        
        # Obtener todas las tablas
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        
        tablas_excluidas = ["historial_respaldos", "configuracion_respaldos", "respaldos_automaticos"]
        
        datos_incrementales = {}
        total_registros = 0
        
        for tabla_item in tablas:
            nombre_tabla = list(tabla_item.values())[0]
            
            if nombre_tabla in tablas_excluidas:
                continue
            
            try:
                # Intentar filtrar por fecha si la tabla tiene campo 'fecha'
                cursor.execute(f"SHOW COLUMNS FROM {nombre_tabla} LIKE 'fecha'")
                tiene_fecha = cursor.fetchone()
                
                if tiene_fecha:
                    cursor.execute(f"""
                        SELECT * FROM {nombre_tabla} 
                        WHERE fecha > %s
                    """, (ultima_fecha,))
                else:
                    # Si no tiene fecha, obtener todas (máx 100)
                    cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT 100")
                
                filas = cursor.fetchall()
                
                if filas:
                    filas_procesadas = []
                    for fila in filas:
                        fila_dict = {}
                        for key, value in fila.items():
                            if isinstance(value, datetime):
                                fila_dict[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                fila_dict[key] = value
                        filas_procesadas.append(fila_dict)
                    
                    datos_incrementales[nombre_tabla] = filas_procesadas
                    total_registros += len(filas_procesadas)
                    
            except Exception as e:
                print(f"Error obteniendo datos incrementales de {nombre_tabla}: {e}")
                continue
        
        return datos_incrementales, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos incrementales: {e}")
        return None, 0


def obtener_datos_diferencial():
    """
    Obtiene datos desde el último respaldo COMPLETO.
    """
    try:
        if cursor is None:
            return None, 0
        
        ultima_fecha = obtener_ultima_fecha_respaldo("completo")
        
        # Si no hay respaldo completo previo, hacer completo
        if ultima_fecha is None:
            return obtener_datos_completos()
        
        # Obtener todas las tablas
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        
        tablas_excluidas = ["historial_respaldos", "configuracion_respaldos", "respaldos_automaticos"]
        
        datos_diferenciales = {}
        total_registros = 0
        
        for tabla_item in tablas:
            nombre_tabla = list(tabla_item.values())[0]
            
            if nombre_tabla in tablas_excluidas:
                continue
            
            try:
                # Intentar filtrar por fecha si la tabla tiene campo 'fecha'
                cursor.execute(f"SHOW COLUMNS FROM {nombre_tabla} LIKE 'fecha'")
                tiene_fecha = cursor.fetchone()
                
                if tiene_fecha:
                    cursor.execute(f"""
                        SELECT * FROM {nombre_tabla} 
                        WHERE fecha >= %s
                    """, (ultima_fecha,))
                else:
                    # Si no tiene fecha, obtener todas
                    cursor.execute(f"SELECT * FROM {nombre_tabla}")
                
                filas = cursor.fetchall()
                
                if filas:
                    filas_procesadas = []
                    for fila in filas:
                        fila_dict = {}
                        for key, value in fila.items():
                            if isinstance(value, datetime):
                                fila_dict[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                fila_dict[key] = value
                        filas_procesadas.append(fila_dict)
                    
                    datos_diferenciales[nombre_tabla] = filas_procesadas
                    total_registros += len(filas_procesadas)
                    
            except Exception as e:
                print(f"Error obteniendo datos diferenciales de {nombre_tabla}: {e}")
                continue
        
        return datos_diferenciales, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos diferenciales: {e}")
        return None, 0


def exportar_pdf_completo(tipo_respaldo="completo"):
    """
    Exporta TODA la base de datos a PDF según el tipo de respaldo.
    """
    try:
        # Obtener datos según tipo
        if tipo_respaldo == "completo":
            datos, total_registros = obtener_datos_completos()
        elif tipo_respaldo == "incremental":
            datos, total_registros = obtener_datos_incremental()
        elif tipo_respaldo == "diferencial":
            datos, total_registros = obtener_datos_diferencial()
        else:
            return None
        
        if datos is None or total_registros == 0:
            return None
        
        # Crear PDF en memoria
        output = io.BytesIO()
        pdf_doc = SimpleDocTemplate(
            output, 
            pagesize=A4,
            rightMargin=30, 
            leftMargin=30,
            topMargin=50, 
            bottomMargin=30
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#3E2723'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#6D4C41'),
            spaceAfter=15,
            spaceBefore=20
        )
        
        # Elementos del documento
        elements = []
        
        # Portada
        title = Paragraph(f"Respaldo de Base de Datos<br/>Nube de Cacao", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Información del respaldo
        info_data = [
            ["Tipo de Respaldo:", tipo_respaldo.upper()],
            ["Fecha de Generación:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Total de Registros:", f"{total_registros:,}"],
            ["Tablas:", f"{len(datos)}"]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFEBE9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # Descripción
        descripciones = {
            "completo": "Este respaldo contiene TODOS los datos de todas las tablas.",
            "incremental": "Este respaldo contiene solo los datos NUEVOS desde el último respaldo.",
            "diferencial": "Este respaldo contiene los datos desde el último respaldo COMPLETO."
        }
        
        desc = Paragraph(f"<b>Descripción:</b> {descripciones.get(tipo_respaldo, '')}", styles['Normal'])
        elements.append(desc)
        elements.append(PageBreak())
        
        # Datos por tabla
        for nombre_tabla, filas in datos.items():
            if not filas:
                continue
            
            # Título de la tabla
            col_title = Paragraph(f"Tabla: {nombre_tabla}", subtitle_style)
            elements.append(col_title)
            
            # Información
            col_info = Paragraph(
                f"Total de registros: <b>{len(filas)}</b>",
                styles['Normal']
            )
            elements.append(col_info)
            elements.append(Spacer(1, 15))
            
            # Crear tabla con los datos (solo primeras 15 filas)
            if filas and len(filas) > 0:
                # Obtener columnas
                columnas = list(filas[0].keys())[:5]  # Máx 5 columnas
                
                data = [columnas]
                
                for fila in filas[:15]:
                    row = [str(fila.get(col, ''))[:30] for col in columnas]
                    data.append(row)
                
                # Anchos de columna
                ancho_total = A4[0] - 2*inch
                col_widths = [ancho_total / len(columnas)] * len(columnas)
                
                table = Table(data, colWidths=col_widths, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6D4C41')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                
                elements.append(table)
                
                if len(filas) > 15:
                    nota = Paragraph(
                        f"<i>Mostrando 15 de {len(filas)} registros...</i>",
                        styles['Italic']
                    )
                    elements.append(nota)
            
            elements.append(Spacer(1, 20))
            elements.append(PageBreak())
        
        # Pie de página
        footer = Paragraph(
            f"<b>Fin del Respaldo</b><br/>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        )
        elements.append(footer)
        
        pdf_doc.build(elements)
        output.seek(0)
        
        # Registrar respaldo
        registrar_respaldo_realizado(tipo_respaldo, "pdf", total_registros)
        
        return output
    
    except Exception as e:
        print(f"Error al exportar PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def exportar_excel_completo(tipo_respaldo="completo"):
    """
    Exporta TODA la base de datos a Excel según el tipo de respaldo.
    """
    try:
        # Obtener datos según tipo
        if tipo_respaldo == "completo":
            datos, total_registros = obtener_datos_completos()
        elif tipo_respaldo == "incremental":
            datos, total_registros = obtener_datos_incremental()
        elif tipo_respaldo == "diferencial":
            datos, total_registros = obtener_datos_diferencial()
        else:
            return None
        
        if datos is None or total_registros == 0:
            return None
        
        # Crear Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Crear una hoja por cada tabla
            for nombre_tabla, filas in datos.items():
                if not filas:
                    continue
                
                df = pd.DataFrame(filas)
                
                # Nombre de hoja válido
                sheet_name = nombre_tabla[:31]
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max() if len(df) > 0 else 0,
                        len(str(col))
                    ) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        
        # Registrar respaldo
        registrar_respaldo_realizado(tipo_respaldo, "excel", total_registros)
        
        return output
    
    except Exception as e:
        print(f"Error al exportar Excel: {e}")
        import traceback
        traceback.print_exc()
        return None


def exportar_sql_completo(tipo_respaldo="completo"):
    """
    Exporta TODA la base de datos a SQL según el tipo de respaldo.
    """
    try:
        # Obtener datos según tipo
        if tipo_respaldo == "completo":
            datos, total_registros = obtener_datos_completos()
        elif tipo_respaldo == "incremental":
            datos, total_registros = obtener_datos_incremental()
        elif tipo_respaldo == "diferencial":
            datos, total_registros = obtener_datos_diferencial()
        else:
            return None
        
        if datos is None or total_registros == 0:
            return None
        
        sql_content = []
        
        # Header
        sql_content.append("-- =====================================================")
        sql_content.append(f"-- Respaldo de Base de Datos - Nube de Cacao")
        sql_content.append(f"-- Tipo: {tipo_respaldo.upper()}")
        sql_content.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_content.append(f"-- Total de registros: {total_registros}")
        sql_content.append(f"-- Total de tablas: {len(datos)}")
        sql_content.append("-- =====================================================")
        sql_content.append("")
        
        # Generar SQL por cada tabla
        for nombre_tabla, filas in datos.items():
            if not filas:
                continue
            
            sql_content.append("")
            sql_content.append(f"-- ==================== {nombre_tabla.upper()} ====================")
            sql_content.append(f"-- Total de registros: {len(filas)}")
            sql_content.append("")
            
            # Obtener estructura de la tabla (si existe)
            try:
                if cursor:
                    cursor.execute(f"SHOW CREATE TABLE {nombre_tabla}")
                    create_info = cursor.fetchone()
                    if create_info:
                        create_stmt = list(create_info.values())[1]
                        sql_content.append(create_stmt + ";")
                        sql_content.append("")
            except:
                # Si no se puede obtener CREATE, crear uno genérico
                columnas = list(filas[0].keys())
                col_defs = ", ".join([f"`{col}` TEXT" for col in columnas])
                sql_content.append(f"CREATE TABLE IF NOT EXISTS `{nombre_tabla}` (")
                sql_content.append(f"    {col_defs}")
                sql_content.append(");")
                sql_content.append("")
            
            # INSERT statements
            for fila in filas:
                columnas = ', '.join([f"`{k}`" for k in fila.keys()])
                
                valores = []
                for v in fila.values():
                    if v is None:
                        valores.append("NULL")
                    elif isinstance(v, (int, float)):
                        valores.append(str(v))
                    else:
                        v_str = str(v).replace("'", "''")
                        valores.append(f"'{v_str}'")
                
                valores_str = ', '.join(valores)
                
                sql_content.append(f"INSERT INTO `{nombre_tabla}` ({columnas}) VALUES ({valores_str});")
            
            sql_content.append("")
        
        # Footer
        sql_content.append("-- =====================================================")
        sql_content.append("-- Fin del respaldo")
        sql_content.append("-- =====================================================")
        
        # Convertir a bytes
        sql_text = "\n".join(sql_content)
        output = io.BytesIO(sql_text.encode('utf-8'))
        output.seek(0)
        
        # Registrar respaldo
        registrar_respaldo_realizado(tipo_respaldo, "sql", total_registros)
        
        return output
    
    except Exception as e:
        print(f"Error al exportar SQL: {e}")
        import traceback
        traceback.print_exc()
        return None