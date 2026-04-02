#!/usr/bin/env python
# Script para verificar los registros de roles/usuarios en MongoDB

import sys
sys.path.insert(0, 'c:\\Users\\ariat\\miniconda3\\envs\\Nube_de_cacao')

from db import db
from datetime import datetime

print("=" * 60)
print("VERIFICANDO REGISTROS EN MONGO_COLLECTIONS")
print("=" * 60)

# Conectar a la colección
collection = db["MONGO_COLLECTIONS"]

# Ver todos los documentos con roll admin o usuario
print("\n1. Buscando registros con roll: 'admin' o 'usuario'")
print("-" * 60)

registros = list(collection.find({"roll": {"$in": ["admin", "usuario"]}}))

print(f"\n✓ Total de registros encontrados: {len(registros)}")

if registros:
    for i, reg in enumerate(registros, 1):
        print(f"\n[Registro {i}]")
        print(f"  _id: {reg.get('_id')}")
        print(f"  roll: {reg.get('roll')}")
        print(f"  correo: {reg.get('correo')}")
        print(f"  nombre: {reg.get('nombre')}")
        print(f"  estado: {reg.get('estado')}")
        print(f"  activo: {reg.get('activo')}")
        print(f"  fecha_creacion: {reg.get('fecha_creacion')}")
else:
    print("\n❌ No se encontraron registros con roll 'admin' o 'usuario'")

# Buscar TODOS los registros en la colección
print("\n" + "=" * 60)
print("2. TODOS los registros en MONGO_COLLECTIONS")
print("-" * 60)

todos = list(collection.find({}))
print(f"\n✓ Total de documentos en la colección: {len(todos)}")

# Agrupar por campos disponibles
campos_roll = {}
for doc in todos:
    roll = doc.get('roll', 'sin-roll')
    if roll not in campos_roll:
        campos_roll[roll] = 0
    campos_roll[roll] += 1

print("\nDistribución por 'roll':")
for roll, count in campos_roll.items():
    print(f"  - {roll}: {count} registros")

print("\n" + "=" * 60)
print("Fin de la verificación")
print("=" * 60)
