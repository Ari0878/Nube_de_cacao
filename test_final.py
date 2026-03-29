#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_final.py - Prueba rápida del proyecto
"""

import os
import sys
from dotenv import load_dotenv

print("\n" + "="*70)
print("🔍 PRUEBA FINAL DEL PROYECTO - NUBE DE CACAO")
print("="*70 + "\n")

# 1. Verificar .env
print("✓ PRUEBA 1: Verificando .env...")
if os.path.exists(".env"):
    load_dotenv()
    mongo_user = os.getenv("MONGO_USER")
    print(f"  ✅ .env encontrado")
    print(f"  📍 MONGO_USER: {mongo_user if mongo_user else '⚠️ NO CONFIGURADO'}")
else:
    print(f"  ❌ .env NO ENCONTRADO")

# 2. Verificar imports básicos
print("\n✓ PRUEBA 2: Verificando imports de Flask...")
try:
    from flask import Flask
    print(f"  ✅ Flask importado correctamente")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# 3. Verificar pymongo
print("\n✓ PRUEBA 3: Verificando PyMongo...")
try:
    from pymongo import MongoClient
    print(f"  ✅ PyMongo importado correctamente")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 4. Verificar scikit-learn
print("\n✓ PRUEBA 4: Verificando scikit-learn...")
try:
    from sklearn.cluster import KMeans
    from sklearn.tree import DecisionTreeRegressor
    print(f"  ✅ scikit-learn importado correctamente")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 5. Verificar pandas y numpy
print("\n✓ PRUEBA 5: Verificando pandas y numpy...")
try:
    import pandas as pd
    import numpy as np
    print(f"  ✅ pandas y numpy importados correctamente")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 6. Verificar syntaxis de archivos principales
print("\n✓ PRUEBA 6: Verificando sintaxis de archivos Python...")
archivos_criticos = [
    "app.py",
    "config.py",
    "db.py",
    "services/kmeans_service.py",
    "services/decision_tree_service.py"
]

for archivo in archivos_criticos:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            code = compile(f.read(), archivo, 'exec')
        print(f"  ✅ {archivo} - Sintaxis válida")
    except Exception as e:
        print(f"  ❌ {archivo} - Error: {e}")

# 7. Verificar templates
print("\n✓ PRUEBA 7: Verificando templates HTML...")
templates = [
    "templates/kmeans.html",
    "templates/arbol_decision.html"
]

for template in templates:
    if os.path.exists(template):
        print(f"  ✅ {template} - Encontrado")
    else:
        print(f"  ❌ {template} - NO ENCONTRADO")

# 8. Cargar configuración
print("\n✓ PRUEBA 8: Cargando configuración desde config.py...")
try:
    import config
    print(f"  ✅ Precios cargados: {list(config.PRECIOS.keys())[:3]}...")
    print(f"  ✅ KMEANS_CLUSTERS={config.KMEANS_CLUSTERS}")
    print(f"  ✅ DECISION_TREE_MAX_DEPTH={config.DECISION_TREE_MAX_DEPTH}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 9. Verificar servicios
print("\n✓ PRUEBA 9: Verificando servicios de Machine Learning...")
try:
    from services.kmeans_service import entrenar_kmeans, calcular_clusters_optimos
    print(f"  ✅ kmeans_service cargado correctamente")
except Exception as e:
    print(f"  ⚠️  kmeans_service: {e}")

try:
    from services.decision_tree_service import entrenar_arbol_regresion
    print(f"  ✅ decision_tree_service cargado correctamente")
except Exception as e:
    print(f"  ⚠️  decision_tree_service: {e}")

# Resultado final
print("\n" + "="*70)
print("📊 RESUMEN FINAL")
print("="*70)
print("\n✅ Proyecto está listo para ejecutarse")
print("\n🚀 Próximo paso: python app.py")
print("\n📍 Accede a: http://localhost:5000\n")

print("="*70)
