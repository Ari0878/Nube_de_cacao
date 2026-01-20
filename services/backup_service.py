# services/backup_service.py
import pandas as pd
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from db import collection
import pymongo


def exportar_excel():
    """
    Exporta todas las ventas a un archivo Excel en memoria.
    Retorna un objeto BytesIO listo para descarga.
    """
    try:
        # Obtener todas las ventas
        ventas = list(collection.find())
        
        if not ventas:
            return None
        
        # Convertir a DataFrame
        df_ventas = []
        for venta in ventas:
            fecha_obj = venta.get('fecha', '')
            if isinstance(fecha_obj, datetime):
                fecha_str = fecha_obj.strftime('%Y-%m-%d %H:%M:%S')
            else:
                fecha_str = str(fecha_obj)
            
            df_ventas.append({
                'ID': str(venta.get('_id', '')),
                'Cliente': venta.get('cliente', ''),
                'Tipo de Café': venta.get('tipo', ''),
                'Cantidad': venta.get('cantidad', 0),
                'Total': venta.get('total', 0.0),
                'Fecha': fecha_str
            })
        
        df = pd.DataFrame(df_ventas)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ventas', index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Ventas']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        return output
        
    except Exception as e:
        print(f"Error al exportar a Excel: {e}")
        return None


def exportar_pdf():
    """
    Exporta todas las ventas a un archivo PDF en memoria.
    Retorna un objeto BytesIO listo para descarga.
    """
    try:
        # Obtener todas las ventas
        ventas = list(collection.find().sort("fecha", -1))
        
        if not ventas:
            return None
        
        # Crear PDF en memoria
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, 
                              rightMargin=30, leftMargin=30,
                              topMargin=50, bottomMargin=30)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#3E2723'),
            spaceAfter=30,
            alignment=1  # Centro
        )
        
        # Elementos del documento
        elements = []
        
        # Título
        title = Paragraph("Historial de Ventas - Nube de Cacao", title_style)
        elements.append(title)
        
        # Fecha de generación
        fecha_generacion = Paragraph(
            f"<b>Fecha de generación:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        )
        elements.append(fecha_generacion)
        elements.append(Spacer(1, 20))
        
        # Tabla de datos
        data = [['Cliente', 'Tipo', 'Cantidad', 'Total', 'Fecha']]
        
        for venta in ventas:
            fecha_str = venta.get('fecha', '').strftime('%Y-%m-%d %H:%M') if isinstance(venta.get('fecha'), datetime) else str(venta.get('fecha', ''))
            data.append([
                str(venta.get('cliente', '')),
                str(venta.get('tipo', '')),
                str(venta.get('cantidad', 0)),
                f"${venta.get('total', 0.0):.2f}",
                fecha_str
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1.5*inch])
        
        # Estilo de tabla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6D4C41')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EFEBE9')]),
        ]))
        
        elements.append(table)
        
        # Resumen
        elements.append(Spacer(1, 30))
        total_ventas = sum(v.get('total', 0) for v in ventas)
        resumen = Paragraph(
            f"<b>Total de ventas:</b> {len(ventas)} | <b>Ingresos totales:</b> ${total_ventas:.2f}",
            styles['Normal']
        )
        elements.append(resumen)
        
        # Construir PDF
        doc.build(elements)
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"Error al exportar a PDF: {e}")
        return None


def exportar_sql():
    """
    Exporta todas las ventas como script SQL (INSERT statements).
    Retorna un objeto BytesIO con el contenido SQL.
    """
    try:
        # Obtener todas las ventas
        ventas = list(collection.find())
        
        if not ventas:
            return None
        
        # Crear script SQL
        sql_content = []
        
        # Header
        sql_content.append("-- Respaldo de Base de Datos - Nube de Cacao")
        sql_content.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_content.append("-- Total de registros: {}".format(len(ventas)))
        sql_content.append("")
        sql_content.append("-- Crear tabla si no existe")
        sql_content.append("CREATE TABLE IF NOT EXISTS ventas (")
        sql_content.append("    id VARCHAR(255) PRIMARY KEY,")
        sql_content.append("    cliente VARCHAR(255),")
        sql_content.append("    tipo VARCHAR(100),")
        sql_content.append("    cantidad INT,")
        sql_content.append("    total DECIMAL(10, 2),")
        sql_content.append("    fecha DATETIME")
        sql_content.append(");")
        sql_content.append("")
        sql_content.append("-- Datos")
        
        # INSERT statements
        for venta in ventas:
            id_venta = str(venta.get('_id', ''))
            cliente = str(venta.get('cliente', '')).replace("'", "''")
            tipo = str(venta.get('tipo', '')).replace("'", "''")
            cantidad = venta.get('cantidad', 0)
            total = venta.get('total', 0.0)
            
            fecha = venta.get('fecha', '')
            if isinstance(fecha, datetime):
                fecha_str = fecha.strftime('%Y-%m-%d %H:%M:%S')
            else:
                fecha_str = str(fecha)
            
            insert = f"INSERT INTO ventas (id, cliente, tipo, cantidad, total, fecha) VALUES ('{id_venta}', '{cliente}', '{tipo}', {cantidad}, {total:.2f}, '{fecha_str}');"
            sql_content.append(insert)
        
        # Convertir a bytes
        sql_text = "\n".join(sql_content)
        output = io.BytesIO(sql_text.encode('utf-8'))
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"Error al exportar a SQL: {e}")
        return None


def obtener_estadisticas_backup():
    """
    Retorna estadísticas útiles sobre la base de datos.
    """
    try:
        total_registros = collection.count_documents({})
        
        # Total de ingresos
        pipeline = [
            {"$group": {
                "_id": None,
                "total_ingresos": {"$sum": "$total"},
                "total_cantidad": {"$sum": "$cantidad"}
            }}
        ]
        
        resultado = list(collection.aggregate(pipeline))
        
        if resultado:
            total_ingresos = resultado[0].get('total_ingresos', 0)
            total_cantidad = resultado[0].get('total_cantidad', 0)
        else:
            total_ingresos = 0
            total_cantidad = 0
        
        # Última venta
        ultima_venta = collection.find_one(sort=[("fecha", pymongo.DESCENDING)])
        fecha_ultima = None
        if ultima_venta and 'fecha' in ultima_venta:
            if isinstance(ultima_venta['fecha'], datetime):
                fecha_ultima = ultima_venta['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'total_registros': total_registros,
            'total_ingresos': total_ingresos,
            'total_cantidad': total_cantidad,
            'fecha_ultima_venta': fecha_ultima
        }
        
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return {
            'total_registros': 0,
            'total_ingresos': 0,
            'total_cantidad': 0,
            'fecha_ultima_venta': None
        }