#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
debug_ml_detailed.py - Debug detallado de cada servicio ML
"""

import sys
import os
from dotenv import load_dotenv
import traceback

# Cargar variables de entorno
load_dotenv()

# ============ K-MEANS DEBUG ============
print("\n" + "="*70)
print("🔍 DEBUG K-MEANS")
print("="*70)
try:
    print("\n1. Importando módulos...")
    from services.kmeans_service import obtener_datos_para_kmeans, entrenar_kmeans
    print("   ✓ Importados correctamente")
    
    print("\n2. Obteniendo datos...")
    X_scaled, df_kmeans, scaler = obtener_datos_para_kmeans()
    print(f"   X_scaled tipo: {type(X_scaled)}, shape: {X_scaled.shape if X_scaled is not None else 'None'}")
    print(f"   df_kmeans tipo: {type(df_kmeans)}, len: {len(df_kmeans) if df_kmeans is not None else 'None'}")
    
    if X_scaled is not None:
        print("\n3. Entrenando modelo...")
        kmeans_result = entrenar_kmeans(3)
        print(f"   Resultado: {kmeans_result}")
    else:
        print("   ❌ X_scaled es None - no hay datos!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()

# ============ REGRESIÓN MÚLTIPLE DEBUG ============
print("\n" + "="*70)
print("🔍 DEBUG REGRESIÓN MÚLTIPLE")
print("="*70)
try:
    print("\n1. Importando módulos...")
    from services.regresion_multiple_service import obtener_datos_ventas_multiple, entrenar_modelo_multiple
    print("   ✓ Importados correctamente")
    
    print("\n2. Obteniendo datos...")
    datos = obtener_datos_ventas_multiple()
    print(f"   Datos tipo: {type(datos)}, len: {len(datos) if datos is not None else 'None'}")
    
    if datos:
        print("\n3. Entrenando modelo...")
        result = entrenar_modelo_multiple()
        print(f"   Resultado: {result}")
    else:
        print("   ❌ No hay datos - obtener_datos_ventas_multiple() retornó None o vacío!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()

# ============ REGRESIÓN POLINÓMICA DEBUG ============
print("\n" + "="*70)
print("🔍 DEBUG REGRESIÓN POLINÓMICA")
print("="*70)
try:
    print("\n1. Importando módulos...")
    from services.regresion_polinomica_service import obtener_datos_ventas_polinomica, entrenar_modelo_polinomico
    print("   ✓ Importados correctamente")
    
    print("\n2. Obteniendo datos...")
    datos = obtener_datos_ventas_polinomica()
    print(f"   Datos tipo: {type(datos)}, valores: {datos if datos else 'None'}")
    
    if datos:
        print("\n3. Entrenando modelo...")
        result = entrenar_modelo_polinomico()
        print(f"   Resultado: {result}")
    else:
        print("   ❌ No hay datos - obtener_datos_ventas_polinomica() retornó None!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()

# ============ ÁRBOL DE DECISIÓN DEBUG ============
print("\n" + "="*70)
print("🔍 DEBUG ÁRBOL DE DECISIÓN")
print("="*70)
try:
    print("\n1. Importando módulos...")
    from services.decision_tree_service import obtener_datos_para_arbol, entrenar_arbol_regresion
    print("   ✓ Importados correctamente")
    
    print("\n2. Obteniendo datos...")
    resultado = obtener_datos_para_arbol()
    print(f"   Resultado tipo: {type(resultado)}, valores retornados: {len(resultado) if resultado else 0}")
    if resultado:
        df, otro = resultado
        print(f"   df: tipo={type(df)}, len={len(df) if df is not None else 'None'}")
        print(f"   otro: {otro}")
    
    if resultado and resultado[0] is not None:
        print("\n3. Entrenando modelo...")
        result = entrenar_arbol_regresion()
        print(f"   Resultado: {result}")
    else:
        print("   ❌ No hay datos - obtener_datos_para_arbol() retornó (None, None)!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()

print("\n" + "="*70)
print("FIN DEL DEBUG DETALLADO")
print("="*70)
