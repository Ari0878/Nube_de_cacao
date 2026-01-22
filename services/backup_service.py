# services/backup_service.py

import os
import json
from datetime import datetime
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from db import collection, db
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
        "registros_respaldados": []
    }


def guardar_metadata(metadata):
    """Guarda el metadata de respaldos"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, ensure_ascii=False, indent=2, fp=f)


def generar_backup_completo():
    """
    Genera un respaldo completo de todas las ventas
    Retorna: (datos, metadata_actualizado)
    """
    ventas = list(collection.find({}))
    
    # Convertir ObjectId a string
    for venta in ventas:
        venta["_id"] = str(venta["_id"])
        if isinstance(venta.get("fecha"), datetime):
            venta["fecha"] = venta["fecha"].isoformat()
    
    # Actualizar metadata
    metadata = cargar_metadata()
    metadata["ultimo_completo"] = datetime.now().isoformat()
    metadata["registros_respaldados"] = [str(v["_id"]) for v in ventas]
    guardar_metadata(metadata)
    
    return ventas, len(ventas)


def generar_backup_incremental():
    """
    Genera un respaldo incremental (solo registros nuevos desde el último respaldo)
    Retorna: (datos, cantidad)
    """
    metadata = cargar_metadata()
    
    # Si no hay respaldo previo, hacer completo
    if not metadata.get("ultimo_incremental") and not metadata.get("ultimo_completo"):
        return generar_backup_completo()
    
    # Obtener la fecha del último respaldo
    ultimo_respaldo = metadata.get("ultimo_incremental") or metadata.get("ultimo_completo")
    fecha_ultimo = datetime.fromisoformat(ultimo_respaldo)
    
    # Obtener solo registros nuevos
    ventas = list(collection.find({"fecha": {"$gt": fecha_ultimo}}))
    
    for venta in ventas:
        venta["_id"] = str(venta["_id"])
        if isinstance(venta.get("fecha"), datetime):
            venta["fecha"] = venta["fecha"].isoformat()
    
    # Actualizar metadata
    metadata["ultimo_incremental"] = datetime.now().isoformat()
    metadata["registros_respaldados"].extend([str(v["_id"]) for v in ventas])
    metadata["registros_respaldados"] = list(set(metadata["registros_respaldados"]))
    guardar_metadata(metadata)
    
    return ventas, len(ventas)


def generar_backup_diferencial():
    """
    Genera un respaldo diferencial (cambios desde el último respaldo completo)
    Retorna: (datos, cantidad)
    """
    metadata = cargar_metadata()
    
    # Si no hay respaldo completo, hacer uno
    if not metadata.get("ultimo_completo"):
        return generar_backup_completo()
    
    fecha_completo = datetime.fromisoformat(metadata["ultimo_completo"])
    
    # Obtener registros desde el último completo
    ventas = list(collection.find({"fecha": {"$gt": fecha_completo}}))
    
    for venta in ventas:
        venta["_id"] = str(venta["_id"])
        if isinstance(venta.get("fecha"), datetime):
            venta["fecha"] = venta["fecha"].isoformat()
    
    # Actualizar metadata
    metadata["ultimo_diferencial"] = datetime.now().isoformat()
    guardar_metadata(metadata)
    
    return ventas, len(ventas)


def generar_excel(ventas, tipo_backup):
    """
    Genera un archivo Excel con los datos de respaldo
    Retorna: BytesIO con el contenido del Excel
    """
    if not ventas:
        # Crear DataFrame vacío con columnas
        df = pd.DataFrame(columns=["_id", "cliente", "tipo", "cantidad", "total", "fecha"])
    else:
        df = pd.DataFrame(ventas)
    
    # Crear archivo en memoria
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Ventas', index=False)
        
        # Agregar hoja con información del respaldo
        info_df = pd.DataFrame({
            'Información del Respaldo': [
                'Tipo de Respaldo',
                'Fecha de Generación',
                'Total de Registros',
                'Sistema'
            ],
            'Valor': [
                tipo_backup.upper(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                len(ventas),
                'Nube de Cacao - Sistema de Ventas'
            ]
        })
        info_df.to_excel(writer, sheet_name='Info Respaldo', index=False)
    
    output.seek(0)
    return output


def generar_pdf(ventas, tipo_backup):
    """
    Genera un archivo PDF con los datos de respaldo
    Retorna: BytesIO con el contenido del PDF
    """
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#4A2C2A'),
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    # Título
    titulo = Paragraph(f"Respaldo de Ventas - {tipo_backup.upper()}", titulo_style)
    elementos.append(titulo)
    
    # Información del respaldo
    info_data = [
        ['Fecha de Generación:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ['Tipo de Respaldo:', tipo_backup.upper()],
        ['Total de Registros:', str(len(ventas))],
        ['Sistema:', 'Nube de Cacao']
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5E6D3')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4A2C2A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elementos.append(info_table)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Tabla de ventas
    if ventas:
        # Encabezados
        datos_tabla = [['Cliente', 'Tipo', 'Cantidad', 'Total', 'Fecha']]
        
        # Datos
        for venta in ventas[:100]:  # Limitar a 100 registros para el PDF
            datos_tabla.append([
                venta.get('cliente', 'N/A'),
                venta.get('tipo', 'N/A'),
                str(venta.get('cantidad', 0)),
                f"${venta.get('total', 0):.2f}",
                venta.get('fecha', 'N/A')[:19] if isinstance(venta.get('fecha'), str) else 'N/A'
            ])
        
        tabla = Table(datos_tabla, colWidths=[1.5*inch, 1.2*inch, 0.8*inch, 0.8*inch, 1.5*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A2C2A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elementos.append(tabla)
        
        if len(ventas) > 100:
            nota = Paragraph(f"<i>Nota: Se muestran los primeros 100 de {len(ventas)} registros totales.</i>", 
                           styles['Normal'])
            elementos.append(Spacer(1, 0.2*inch))
            elementos.append(nota)
    else:
        sin_datos = Paragraph("<i>No hay registros para mostrar en este respaldo.</i>", styles['Normal'])
        elementos.append(sin_datos)
    
    doc.build(elementos)
    output.seek(0)
    return output


def generar_sql(ventas, tipo_backup):
    """
    Genera un archivo SQL con los datos de respaldo
    Retorna: BytesIO con el contenido SQL
    """
    output = BytesIO()
    
    # Escribir encabezado
    sql_content = f"""-- ============================================
-- Respaldo de Base de Datos - Nube de Cacao
-- Tipo: {tipo_backup.upper()}
-- Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Total de Registros: {len(ventas)}
-- ============================================

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS ventas (
    _id VARCHAR(50) PRIMARY KEY,
    cliente VARCHAR(255),
    tipo VARCHAR(100),
    cantidad INT,
    total DECIMAL(10, 2),
    fecha DATETIME
);

"""
    
    # Agregar instrucciones INSERT
    if ventas:
        sql_content += "-- Insertar datos\n"
        for venta in ventas:
            cliente = venta.get('cliente', '').replace("'", "''")
            tipo = venta.get('tipo', '').replace("'", "''")
            cantidad = venta.get('cantidad', 0)
            total = venta.get('total', 0.0)
            fecha = venta.get('fecha', datetime.now().isoformat())[:19].replace('T', ' ')
            _id = venta.get('_id', '')
            
            sql_content += f"""INSERT INTO ventas (_id, cliente, tipo, cantidad, total, fecha) 
VALUES ('{_id}', '{cliente}', '{tipo}', {cantidad}, {total}, '{fecha}');
"""
    else:
        sql_content += "-- No hay registros para insertar\n"
    
    sql_content += "\n-- Fin del respaldo\n"
    
    output.write(sql_content.encode('utf-8'))
    output.seek(0)
    return output


def obtener_info_respaldos():
    """
    Retorna información sobre los respaldos realizados
    """
    metadata = cargar_metadata()
    
    return {
        "ultimo_completo": metadata.get("ultimo_completo"),
        "ultimo_incremental": metadata.get("ultimo_incremental"),
        "ultimo_diferencial": metadata.get("ultimo_diferencial"),
        "total_registros": len(metadata.get("registros_respaldados", []))
    }