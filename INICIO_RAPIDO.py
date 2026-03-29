#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUÍA DE INICIO RÁPIDO - Nube de Cacao
======================================

Sigue estos pasos para que tu proyecto funcione correctamente:
"""

import os
import sys

print("=" * 70)
print("🍫 GUÍA DE INICIO RÁPIDO - NUBE DE CACAO 🍫")
print("=" * 70)

checklist = {
    "✅ .env configurado": os.path.exists(".env"),
    "✅ app.py existe": os.path.exists("app.py"),
    "✅ config.py existe": os.path.exists("config.py"),
    "✅ db.py existe": os.path.exists("db.py"),
    "✅ services/kmeans_service.py": os.path.exists("services/kmeans_service.py"),
    "✅ services/decision_tree_service.py": os.path.exists("services/decision_tree_service.py"),
    "✅ templates/kmeans.html": os.path.exists("templates/kmeans.html"),
    "✅ templates/arbol_decision.html": os.path.exists("templates/arbol_decision.html"),
}

print("\n📋 VERIFICACIÓN DE ARCHIVOS:\n")
for item, status in checklist.items():
    icon = "✅" if status else "❌"
    print(f"  {icon} {item}")

print("\n" + "=" * 70)
print("📝 PASOS PARA COMENZAR:")
print("=" * 70)

pasos = [
    "1. CONFIGURA TU .env FILE",
    "   - Abre el archivo .env en la raíz del proyecto",
    "   - Reemplaza tus credenciales MongoDB Atlas:",
    "     MONGO_USER=tu_usuario",
    "     MONGO_PASSWORD=tu_contraseña",
    "     MONGO_CLUSTER=tu_cluster.mongodb.net",
    "     MONGO_DB=nube_de_cacao",
    "",
    "2. INSTALA DEPENDENCIAS (si es necesario)",
    "   pip install flask pymongo python-dotenv scikit-learn pandas numpy",
    "",
    "3. EJECUTA LA APLICACIÓN",
    "   python app.py",
    "",
    "4. ACCEDE EN TU NAVEGADOR",
    "   http://localhost:5000",
    "",
    "5. INICIA SESIÓN",
    "   - Usa credenciales de usuarios en tu MongoDB",
    "   - Si no tienes, crea uno en /register",
]

for paso in pasos:
    print(f"  {paso}")

print("\n" + "=" * 70)
print("🚀 NUEVAS FUNCIONALIDADES AGREGADAS:")
print("=" * 70)

features = [
    "✨ K-Means Clustering: /kmeans",
    "   - Agrupa tus datos de ventas automáticamente",
    "   - Calcula Silhouette Score",
    "   - Encuentra número óptimo de clusters",
    "",
    "✨ Árbol de Decisión: /arbol-decision",
    "   - Regresión para predecir totales de ventas",
    "   - Clasificación para tipos de productos",
    "   - Importancia de features analizadas",
    "",
    "✨ Configuración Centralizada",
    "   - Todo se carga desde .env",
    "   - Fácil de personalizar",
    "   - Configuración segura",
]

for feature in features:
    print(f"  {feature}")

print("\n" + "=" * 70)
print("🔍 PROBLEMAS CORREGIDOS:")
print("=" * 70)

fixes = [
    "❌ Typo 'vventas' → ✅ 'ventas'",
    "❌ 'collection' no definido → ✅ 'ventas_col'",
    "❌ Importaciones faltantes → ✅ kmeans_service y decision_tree_service",
    "❌ Código duplicado → ✅ Eliminado",
    "❌ config.py vacío → ✅ Configuración completa",
]

for fix in fixes:
    print(f"  {fix}")

print("\n" + "=" * 70)
print("📊 RUTAS DISPONIBLES:")
print("=" * 70)

routes = [
    "General:",
    "  /login - Inicio de sesión",
    "  /dashboard - Panel principal",
    "  /perfil - Perfil de usuario",
    "",
    "Machine Learning:",
    "  /regresion - Regresión lineal simple",
    "  /regresion-multiple - Regresión múltiple",
    "  /kmeans - K-Means Clustering",
    "  /arbol-decision - Árbol de Decisión",
    "",
    "Respaldos:",
    "  /respaldos - Panel de respaldos",
    "  /respaldos/centro-descargas - Descargar backups",
    "  /respaldos/configuracion - Configurar automáticos",
]

for route in routes:
    print(f"  {route}")

print("\n" + "=" * 70)
print("💡 TIPS:")
print("=" * 70)

tips = [
    "• Necesitas al menos 5 registros de ventas para entrenar los modelos",
    "• Los parámetros de ML se pueden personalizar en el .env",
    "• Los modelos se entrenan con cada solicitud (no se cacheam)",
    "• Verifica la consola para mensajes de debug y errores",
    "• Los precios se cargan desde .env para fácil actualización",
]

for tip in tips:
    print(f"  {tip}")

print("\n" + "=" * 70)
print("✅ ¡LISTO PARA COMENZAR! 🎉")
print("=" * 70)
print("\nEjecuta: python app.py")
print("Luego accede a: http://localhost:5000\n")
