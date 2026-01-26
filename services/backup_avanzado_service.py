# services/backup_avanzado_service.py
import io
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from db import db, collection, usuarios_col
import pandas as pd


def obtener_ultima_fecha_respaldo(tipo_respaldo):
    """
    Obtiene la fecha del último respaldo realizado de un tipo específico.
    Se usa para respaldos incrementales y diferenciales.
    """
    try:
        if db is None:
            return None
        
        respaldos_col = db["historial_respaldos"]
        ultimo = respaldos_col.find_one(
            {"tipo_respaldo": tipo_respaldo, "exitoso": True},
            sort=[("fecha", -1)]
        )
        
        if ultimo and "fecha" in ultimo:
            return ultimo["fecha"]
        return None
    except:
        return None


def registrar_respaldo_realizado(tipo_respaldo, tipo_formato, total_registros):
    """Registra el respaldo en el historial"""
    try:
        if db is None:
            return
        
        respaldos_col = db["historial_respaldos"]
        respaldos_col.insert_one({
            "tipo_respaldo": tipo_respaldo,
            "tipo_formato": tipo_formato,
            "total_registros": total_registros,
            "fecha": datetime.now(),
            "exitoso": True
        })
    except Exception as e:
        print(f"Error al registrar respaldo: {e}")


def obtener_datos_completos():
    """
    Obtiene TODOS los datos de TODAS las colecciones de la base de datos.
    """
    try:
        if db is None:
            return None, 0
        
        datos_completos = {}
        
        # Obtener todas las colecciones
        colecciones = db.list_collection_names()
        
        # Excluir colecciones del sistema
        colecciones_excluidas = ["system.indexes", "historial_respaldos"]
        colecciones = [c for c in colecciones if c not in colecciones_excluidas]
        
        total_registros = 0
        
        for nombre_coleccion in colecciones:
            col = db[nombre_coleccion]
            documentos = list(col.find())
            
            # Convertir ObjectId a string
            for documento in documentos:
                if "_id" in documento:
                    documento["_id"] = str(documento["_id"])
                # Convertir fechas a string
                for key, value in documento.items():
                    if isinstance(value, datetime):
                        documento[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            
            datos_completos[nombre_coleccion] = documentos
            total_registros += len(documentos)
        
        return datos_completos, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos completos: {e}")
        return None, 0


def obtener_datos_incremental():
    """
    Obtiene solo los datos NUEVOS desde el último respaldo incremental.
    """
    try:
        if db is None:
            return None, 0
        
        ultima_fecha = obtener_ultima_fecha_respaldo("incremental")
        
        # Si no hay respaldo previo, hacer completo
        if ultima_fecha is None:
            return obtener_datos_completos()
        
        datos_incrementales = {}
        total_registros = 0
        
        colecciones = db.list_collection_names()
        colecciones_excluidas = ["system.indexes", "historial_respaldos"]
        colecciones = [c for c in colecciones if c not in colecciones_excluidas]
        
        for nombre_coleccion in colecciones:
            col = db[nombre_coleccion]
            
            # Buscar documentos creados después de la última fecha
            try:
                documentos = list(col.find({"fecha": {"$gt": ultima_fecha}}))
            except:
                documentos = []
            
            # Convertir ObjectId y fechas
            for documento in documentos:
                if "_id" in documento:
                    documento["_id"] = str(documento["_id"])
                for key, value in documento.items():
                    if isinstance(value, datetime):
                        documento[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            
            if documentos:
                datos_incrementales[nombre_coleccion] = documentos
                total_registros += len(documentos)
        
        return datos_incrementales, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos incrementales: {e}")
        return None, 0


def obtener_datos_diferencial():
    """
    Obtiene datos modificados desde el último respaldo COMPLETO.
    """
    try:
        if db is None:
            return None, 0
        
        ultima_fecha = obtener_ultima_fecha_respaldo("completo")
        
        # Si no hay respaldo completo previo, hacer completo
        if ultima_fecha is None:
            return obtener_datos_completos()
        
        datos_diferenciales = {}
        total_registros = 0
        
        colecciones = db.list_collection_names()
        colecciones_excluidas = ["system.indexes", "historial_respaldos"]
        colecciones = [c for c in colecciones if c not in colecciones_excluidas]
        
        for nombre_coleccion in colecciones:
            col = db[nombre_coleccion]
            
            # Obtener documentos modificados/creados desde última fecha
            try:
                documentos = list(col.find({"fecha": {"$gte": ultima_fecha}}))
            except:
                documentos = []
            
            # Convertir ObjectId y fechas
            for documento in documentos:
                if "_id" in documento:
                    documento["_id"] = str(documento["_id"])
                for key, value in documento.items():
                    if isinstance(value, datetime):
                        documento[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            
            if documentos:
                datos_diferenciales[nombre_coleccion] = documentos
                total_registros += len(documentos)
        
        return datos_diferenciales, total_registros
    
    except Exception as e:
        print(f"Error al obtener datos diferenciales: {e}")
        return None, 0


def exportar_pdf_completo(tipo_respaldo="completo"):
    """
    Exporta TODA la base de datos a PDF según el tipo de respaldo.
    
    Args:
        tipo_respaldo: "completo", "incremental", "diferencial"
    """
    try:
        # Obtener datos según tipo de respaldo
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
            ["Colecciones:", f"{len(datos)}"]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFEBE9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # Descripción del tipo de respaldo
        descripciones = {
            "completo": "Este respaldo contiene TODOS los datos de todas las colecciones de la base de datos.",
            "incremental": "Este respaldo contiene solo los datos NUEVOS desde el último respaldo incremental.",
            "diferencial": "Este respaldo contiene los datos modificados desde el último respaldo COMPLETO."
        }
        
        desc = Paragraph(f"<b>Descripción:</b> {descripciones.get(tipo_respaldo, '')}", styles['Normal'])
        elements.append(desc)
        elements.append(PageBreak())
        
        # Datos por colección
        for nombre_coleccion, documentos in datos.items():
            if not documentos:
                continue
            
            # Título de la colección
            col_title = Paragraph(f"Colección: {nombre_coleccion}", subtitle_style)
            elements.append(col_title)
            
            # Información de la colección
            col_info = Paragraph(
                f"Total de registros: <b>{len(documentos)}</b>",
                styles['Normal']
            )
            elements.append(col_info)
            elements.append(Spacer(1, 15))
            
            # Crear tabla con los datos
            if nombre_coleccion == "ventas":
                # Tabla específica para ventas
                data = [['Cliente', 'Tipo', 'Cantidad', 'Total', 'Fecha']]
                for documento in documentos:
                    data.append([
                        str(documento.get('cliente', 'N/A'))[:20],
                        str(documento.get('tipo', 'N/A')),
                        str(documento.get('cantidad', 0)),
                        f"${documento.get('total', 0):.2f}",
                        str(documento.get('fecha', 'N/A'))[:16]
                    ])
                
                col_widths = [1.5*inch, 1*inch, 0.8*inch, 1*inch, 1.2*inch]
            
            elif nombre_coleccion == "usuarios":
                # Tabla específica para usuarios
                data = [['Email', 'Nombre', 'Teléfono', 'Fecha Registro']]
                for documento in documentos:
                    data.append([
                        str(documento.get('email', 'N/A'))[:25],
                        str(documento.get('nombre', 'N/A'))[:20],
                        str(documento.get('telefono', 'N/A')),
                        str(documento.get('fecha_registro', 'N/A'))[:16]
                    ])
                
                col_widths = [2*inch, 1.5*inch, 1*inch, 1.2*inch]
            
            else:
                # Tabla genérica para otras colecciones
                if documentos:
                    # Obtener las primeras 5 claves (excluyendo _id)
                    keys = [k for k in documentos[0].keys() if k != '_id'][:5]
                    data = [keys]
                    
                    for documento in documentos:
                        row = [str(documento.get(k, 'N/A'))[:25] for k in keys]
                        data.append(row)
                    
                    # Distribuir ancho equitativamente
                    col_widths = [6.5*inch / len(keys)] * len(keys)
                else:
                    continue
            
            # Limitar a 30 registros por página
            max_registros = 30
            if len(data) > max_registros + 1:
                data_truncated = data[:max_registros + 1]
                table = Table(data_truncated, colWidths=col_widths)
                
                # Estilo de tabla
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6D4C41')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EFEBE9')]),
                ]))
                
                elements.append(table)
                
                # Mensaje de truncamiento
                truncate_msg = Paragraph(
                    f"<i>Mostrando {max_registros} de {len(data)-1} registros...</i>",
                    styles['Italic']
                )
                elements.append(truncate_msg)
            else:
                table = Table(data, colWidths=col_widths)
                
                # Estilo de tabla
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6D4C41')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EFEBE9')]),
                ]))
                
                elements.append(table)
            
            elements.append(Spacer(1, 20))
            elements.append(PageBreak())
        
        # Pie de página final
        footer = Paragraph(
            f"<b>Fin del Respaldo</b><br/>Generado automáticamente por Nube de Cacao<br/>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        )
        elements.append(footer)
        
        # Construir PDF
        pdf_doc.build(elements)
        output.seek(0)
        
        # Registrar respaldo
        registrar_respaldo_realizado(tipo_respaldo, "pdf", total_registros)
        
        return output
    
    except Exception as e:
        print(f"Error al exportar PDF completo: {e}")
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
            # Crear una hoja por cada colección
            for nombre_coleccion, documentos in datos.items():
                if not documentos:
                    continue
                
                df = pd.DataFrame(documentos)
                
                # Nombre de hoja válido (max 31 caracteres)
                sheet_name = nombre_coleccion[:31]
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        
        # Registrar respaldo
        registrar_respaldo_realizado(tipo_respaldo, "excel", total_registros)
        
        return output
    
    except Exception as e:
        print(f"Error al exportar Excel completo: {e}")
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
        sql_content.append(f"-- Total de colecciones: {len(datos)}")
        sql_content.append("-- =====================================================")
        sql_content.append("")
        
        # Generar SQL por cada colección
        for nombre_coleccion, documentos in datos.items():
            if not documentos:
                continue
            
            sql_content.append("")
            sql_content.append(f"-- ==================== {nombre_coleccion.upper()} ====================")
            sql_content.append(f"-- Total de registros: {len(documentos)}")
            sql_content.append("")
            
            # Crear tabla
            if nombre_coleccion == "ventas":
                sql_content.append("CREATE TABLE IF NOT EXISTS ventas (")
                sql_content.append("    id VARCHAR(255) PRIMARY KEY,")
                sql_content.append("    cliente VARCHAR(255),")
                sql_content.append("    tipo VARCHAR(100),")
                sql_content.append("    cantidad INT,")
                sql_content.append("    total DECIMAL(10, 2),")
                sql_content.append("    fecha DATETIME")
                sql_content.append(");")
            elif nombre_coleccion == "usuarios":
                sql_content.append("CREATE TABLE IF NOT EXISTS usuarios (")
                sql_content.append("    id VARCHAR(255) PRIMARY KEY,")
                sql_content.append("    email VARCHAR(255) UNIQUE,")
                sql_content.append("    nombre VARCHAR(255),")
                sql_content.append("    telefono VARCHAR(50),")
                sql_content.append("    fecha_registro DATETIME")
                sql_content.append(");")
            else:
                # Tabla genérica
                sql_content.append(f"CREATE TABLE IF NOT EXISTS {nombre_coleccion} (")
                sql_content.append("    id VARCHAR(255) PRIMARY KEY,")
                sql_content.append("    data JSON")
                sql_content.append(");")
            
            sql_content.append("")
            
            # INSERT statements
            for documento in documentos:
                if nombre_coleccion == "ventas":
                    id_val = str(documento.get('_id', ''))
                    cliente = str(documento.get('cliente', '')).replace("'", "''")
                    tipo = str(documento.get('tipo', '')).replace("'", "''")
                    cantidad = documento.get('cantidad', 0)
                    total = documento.get('total', 0.0)
                    fecha = str(documento.get('fecha', ''))
                    
                    insert = f"INSERT INTO ventas (id, cliente, tipo, cantidad, total, fecha) VALUES ('{id_val}', '{cliente}', '{tipo}', {cantidad}, {total:.2f}, '{fecha}');"
                    sql_content.append(insert)
                
                elif nombre_coleccion == "usuarios":
                    id_val = str(documento.get('_id', ''))
                    email = str(documento.get('email', '')).replace("'", "''")
                    nombre = str(documento.get('nombre', '')).replace("'", "''")
                    telefono = str(documento.get('telefono', ''))
                    fecha_reg = str(documento.get('fecha_registro', ''))
                    
                    insert = f"INSERT INTO usuarios (id, email, nombre, telefono, fecha_registro) VALUES ('{id_val}', '{email}', '{nombre}', '{telefono}', '{fecha_reg}');"
                    sql_content.append(insert)
                
                else:
                    id_val = str(documento.get('_id', ''))
                    data_json = json.dumps(documento).replace("'", "''")
                    insert = f"INSERT INTO {nombre_coleccion} (id, data) VALUES ('{id_val}', '{data_json}');"
                    sql_content.append(insert)
            
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
        print(f"Error al exportar SQL completo: {e}")
        import traceback
        traceback.print_exc()
        return None