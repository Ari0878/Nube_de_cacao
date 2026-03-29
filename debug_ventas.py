#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
debug_ventas.py - Verificar datos de ventas en MongoDB
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=" * 70)
print("🔍 VERIFICACIÓN DE VENTAS EN MONGODB")
print("=" * 70)

# 1. Intentar conectar a MongoDB
print("\n✓ PASO 1: Conectando a MongoDB...")
try:
    from db import ventas_col
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error en conexión: {e}")
    sys.exit(1)

# 2. Contar documentos
print("\n✓ PASO 2: Contando documentos...")
try:
    count = ventas_col.count_documents({})
    print(f"📊 Total de ventas: {count}")
    
    if count == 0:
        print("⚠️  No hay ventas registradas")
    else:
        print(f"✅ Hay {count} ventas registradas")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Ver un ejemplo de venta
print("\n✓ PASO 3: Mostrando primera venta...")
try:
    sample = ventas_col.find_one()
    if sample:
        print("📋 Estructura de venta:")
        for key, value in sample.items():
            print(f"   - {key}: {value}")
    else:
        print("⚠️  No hay ventas para mostrar")
except Exception as e:
    print(f"❌ Error: {e}")

# 4. Intentar usar el servicio de análisis
print("\n✓ PASO 4: Funcionamiento del análisis...")
try:
    from services.analisis_service import obtener_resumen_ventas
    
    analisis = obtener_resumen_ventas()
    
    if analisis:
        print("✅ Análisis funcionando correctamente")
        print(f"   Total Ingresos: ${analisis.get('total_ingresos', 0):.2f}")
        print(f"   Total Productos: {analisis.get('total_productos', 0)}")
        print(f"   Precio Promedio: ${analisis.get('promedio_precio', 0):.2f}")
        print(f"   Top Producto: {analisis.get('top_producto', {}).get('tipo', 'N/A')}")
        print(f"   Top Cliente: {analisis.get('top_cliente', {}).get('cliente', 'N/A')}")
    else:
        print("❌ El análisis retorna None")
        print("   Esto significa que no hay datos o hay un error")
except Exception as e:
    print(f"❌ Error en análisis: {e}")
    import traceback
    traceback.print_exc()

# 5. Intentar usar regresión
print("\n✓ PASO 5: Verificando modelo de regresión simple...")
try:
    from services.regresion_service import entrenar_modelo_regresion
    
    modelo = entrenar_modelo_regresion()
    
    if modelo:
        print("✅ Modelo de regresión simple entrenado")
        print(f"   R² Score: {modelo.get('r2', 0):.4f}")
        print(f"   RMSE: {modelo.get('rmse', 0):.4f}")
        print(f"   Datos usados: {modelo.get('num_datos', 0)}")
    else:
        print("❌ No se pudo entrenar el modelo de regresión")
        print("   Esto significa que no hay datos suficientes")
except Exception as e:
    print(f"❌ Error en regresión simple: {e}")
    import traceback
    traceback.print_exc()

# 6. K-Means
print("\n✓ PASO 6: Verificando modelo K-Means...")
try:
    from services.kmeans_service import obtener_datos_para_kmeans, entrenar_kmeans
    
    X_scaled, df_kmeans, scaler = obtener_datos_para_kmeans()
    if X_scaled is not None and len(X_scaled) >= 5:
        kmeans_result = entrenar_kmeans(3)
        if kmeans_result and kmeans_result.get('modelo'):
            print("✅ Modelo K-Means entrenado")
            print(f"   Inercia: {kmeans_result.get('inercia', 'N/A'):.4f}")
            print(f"   Datos usados: {len(X_scaled)}")
            print(f"   Silhouette Score: {kmeans_result.get('silhouette', 'N/A')}")
        else:
            print("❌ No se pudo entrenar K-Means")
    else:
        print("❌ No hay suficientes datos para K-Means")
except Exception as e:
    print(f"❌ Error en K-Means: {e}")
    import traceback
    traceback.print_exc()

# 7. Regresión Múltiple
print("\n✓ PASO 7: Verificando modelo Regresión Múltiple...")
try:
    from services.regresion_multiple_service import entrenar_modelo_multiple
    
    regresion_multiple_result = entrenar_modelo_multiple()
    if regresion_multiple_result and regresion_multiple_result.get('r2_score'):
        print("✅ Modelo Regresión Múltiple entrenado")
        print(f"   R² Score: {regresion_multiple_result.get('r2_score', 0):.4f}")
        print(f"   RMSE: {regresion_multiple_result.get('rmse', 0):.4f}")
    else:
        print("❌ No se pudo entrenar Regresión Múltiple")
except Exception as e:
    print(f"❌ Error en Regresión Múltiple: {e}")
    import traceback
    traceback.print_exc()

# 8. Regresión Polinómica
print("\n✓ PASO 8: Verificando modelo Regresión Polinómica...")
try:
    from services.regresion_polinomica_service import entrenar_modelo_polinomico
    
    regresion_poli_result = entrenar_modelo_polinomico()
    if regresion_poli_result and regresion_poli_result.get('r2_score'):
        print("✅ Modelo Regresión Polinómica entrenado")
        print(f"   R² Score: {regresion_poli_result.get('r2_score', 0):.4f}")
        print(f"   RMSE: {regresion_poli_result.get('rmse', 0):.4f}")
    else:
        print("❌ No se pudo entrenar Regresión Polinómica")
except Exception as e:
    print(f"❌ Error en Regresión Polinómica: {e}")
    import traceback
    traceback.print_exc()

# 9. Árbol de Decisión
print("\n✓ PASO 9: Verificando modelo Árbol de Decisión...")
try:
    from services.decision_tree_service import obtener_datos_para_arbol, entrenar_arbol_regresion
    
    resultado_datos = obtener_datos_para_arbol()
    if resultado_datos and resultado_datos[0] is not None and len(resultado_datos[0]) >= 5:
        arbol_result = entrenar_arbol_regresion()
        if arbol_result and arbol_result.get('r2_score'):
            print("✅ Modelo Árbol de Decisión entrenado")
            print(f"   R² Score: {arbol_result.get('r2_score', 0):.4f}")
            print(f"   RMSE: {arbol_result.get('rmse', 0):.4f}")
        else:
            print("❌ No se pudo entrenar Árbol de Decisión")
    else:
        print("❌ No hay suficientes datos para Árbol de Decisión")
except Exception as e:
    print(f"❌ Error en Árbol de Decisión: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("FIN DE DIAGNÓSTICO - TODOS LOS SERVICIOS VERIFICADOS")
print("=" * 70)
