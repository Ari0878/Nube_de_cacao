#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug regresión múltiple"""

from services.regresion_multiple_service import obtener_datos_ventas_multiple, entrenar_modelo_multiple
import traceback

print("=" * 70)
print("DEBUG REGRESIÓN MÚLTIPLE")
print("=" * 70)

print("\n1. Obteniendo datos...")
try:
    X, y, tipo_a_codigo = obtener_datos_ventas_multiple()
    print(f"   ✓ X shape: {X.shape if X is not None else None}")
    print(f"   ✓ y shape: {y.shape if y is not None else None}")
    print(f"   ✓ tipo_a_codigo: {tipo_a_codigo}")
    print(f"   ✓ len(X): {len(X) if X is not None else None}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

print("\n2. Entrenando modelo...")
try:
    modelo = entrenar_modelo_multiple()
    print(f"   Resultado: {modelo}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()
