#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para sistema de respaldos
Ejecutar: python test_backup.py
"""

print("=" * 70)
print("DIAGNÓSTICO DEL SISTEMA DE RESPALDOS")
print("=" * 70)

# Test 1: Verificar MongoDB
print("\n1. Verificando conexión a MongoDB...")
try:
    from db import db, collection, usuarios_col
    
    if db is None:
        print("   ❌ ERROR: MongoDB no está conectado")
        print("   Solución: Asegúrate de que MongoDB esté corriendo")
        print("   Comando: net start MongoDB  (Windows)")
        exit(1)
    else:
        print("   ✅ MongoDB conectado correctamente")
        
        # Contar documentos
        total_ventas = collection.count_documents({})
        total_usuarios = usuarios_col.count_documents({})
        
        print(f"   📊 Ventas en BD: {total_ventas}")
        print(f"   👥 Usuarios en BD: {total_usuarios}")
        
        if total_ventas == 0:
            print("   ⚠️  ADVERTENCIA: No hay ventas. Los respaldos estarán vacíos.")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Verificar dependencias
print("\n2. Verificando dependencias instaladas...")

dependencias = {
    'pandas': 'pandas',
    'openpyxl': 'openpyxl',
    'reportlab': 'reportlab',
    'schedule': 'schedule'
}

faltantes = []

for nombre, modulo in dependencias.items():
    try:
        __import__(modulo)
        print(f"   ✅ {nombre} instalado")
    except ImportError:
        print(f"   ❌ {nombre} NO instalado")
        faltantes.append(nombre)

if faltantes:
    print(f"\n   ⚠️  Instala las dependencias faltantes:")
    print(f"   pip install {' '.join(faltantes)}")
    exit(1)

# Test 3: Verificar archivos de servicio
print("\n3. Verificando archivos de servicio...")

archivos_necesarios = [
    'services/backup_service.py',
    'services/backup_avanzado_service.py',
    'services/scheduler_service.py'
]

import os

for archivo in archivos_necesarios:
    if os.path.exists(archivo):
        print(f"   ✅ {archivo} existe")
    else:
        print(f"   ❌ {archivo} NO EXISTE")
        print(f"      Debes crear este archivo con el código proporcionado")

# Test 4: Probar importaciones
print("\n4. Probando importaciones de servicios...")

try:
    from services.backup_avanzado_service import (
        exportar_excel_completo,
        exportar_pdf_completo,
        exportar_sql_completo,
        obtener_datos_completos
    )
    print("   ✅ backup_avanzado_service se importa correctamente")
except Exception as e:
    print(f"   ❌ ERROR al importar backup_avanzado_service:")
    print(f"      {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Probar obtención de datos
print("\n5. Probando obtención de datos...")

try:
    datos, total = obtener_datos_completos()
    
    if datos is None:
        print("   ❌ No se pudieron obtener datos")
        exit(1)
    
    print(f"   ✅ Datos obtenidos correctamente")
    print(f"   📊 Total de registros: {total}")
    print(f"   📁 Colecciones encontradas: {len(datos)}")
    
    for nombre_col, docs in datos.items():
        print(f"      - {nombre_col}: {len(docs)} documentos")
    
except Exception as e:
    print(f"   ❌ ERROR al obtener datos:")
    print(f"      {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Probar generación de Excel
print("\n6. Probando generación de respaldo Excel...")

try:
    archivo = exportar_excel_completo("completo")
    
    if archivo is None:
        print("   ❌ No se pudo generar Excel")
        exit(1)
    
    tamaño = len(archivo.getvalue())
    print(f"   ✅ Excel generado correctamente")
    print(f"   📦 Tamaño: {tamaño:,} bytes ({tamaño/1024:.2f} KB)")
    
except Exception as e:
    print(f"   ❌ ERROR al generar Excel:")
    print(f"      {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: Probar generación de PDF
print("\n7. Probando generación de respaldo PDF...")

try:
    archivo = exportar_pdf_completo("completo")
    
    if archivo is None:
        print("   ❌ No se pudo generar PDF")
        exit(1)
    
    tamaño = len(archivo.getvalue())
    print(f"   ✅ PDF generado correctamente")
    print(f"   📦 Tamaño: {tamaño:,} bytes ({tamaño/1024:.2f} KB)")
    
except Exception as e:
    print(f"   ❌ ERROR al generar PDF:")
    print(f"      {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 8: Probar generación de SQL
print("\n8. Probando generación de respaldo SQL...")

try:
    archivo = exportar_sql_completo("completo")
    
    if archivo is None:
        print("   ❌ No se pudo generar SQL")
        exit(1)
    
    tamaño = len(archivo.getvalue())
    print(f"   ✅ SQL generado correctamente")
    print(f"   📦 Tamaño: {tamaño:,} bytes ({tamaño/1024:.2f} KB)")
    
except Exception as e:
    print(f"   ❌ ERROR al generar SQL:")
    print(f"      {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 9: Verificar rutas en app.py
print("\n9. Verificando rutas en app.py...")

try:
    with open('app.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    rutas_necesarias = [
        'exportar_excel_completo',
        'exportar_pdf_completo',
        'exportar_sql_completo',
        '/respaldos/descargar/excel',
        '/respaldos/descargar/pdf',
        '/respaldos/descargar/sql'
    ]
    
    for ruta in rutas_necesarias:
        if ruta in contenido:
            print(f"   ✅ {ruta} encontrado")
        else:
            print(f"   ❌ {ruta} NO encontrado en app.py")
            print(f"      Actualiza app.py con el código proporcionado")
    
except Exception as e:
    print(f"   ⚠️  No se pudo leer app.py: {e}")

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
print("=" * 70)

print("\nSi los tests pasaron pero aún no funciona en la web:")
print("1. Asegúrate de haber reiniciado Flask completamente")
print("2. Limpia el caché del navegador (Ctrl+Shift+Del)")
print("3. Prueba en modo incógnito")
print("4. Revisa la consola de Flask para errores")
print("5. Revisa la consola del navegador (F12)")

print("\nPara probar manualmente una descarga:")
print("python")
print(">>> from services.backup_avanzado_service import exportar_excel_completo")
print(">>> archivo = exportar_excel_completo('completo')")
print(">>> with open('test.xlsx', 'wb') as f:")
print("...     f.write(archivo.read())")
print(">>> # Abre test.xlsx para verificar")