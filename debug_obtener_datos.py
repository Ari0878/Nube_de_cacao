#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug detallado de obtener_datos_ventas_multiple"""

import pandas as pd
from db import ventas_col
import traceback

print("=" * 70)
print("DEBUG DETALLADO: obtener_datos_ventas_multiple")
print("=" * 70)

try:
    print("\n1. Obteniendo datos crudos de MongoDB...")
    ventas = list(ventas_col.find({}, {'_id': 0, 'tipo': 1, 'cantidad': 1, 'total': 1, 'fecha': 1}).limit(500))
    print(f"   Registros obtenidos: {len(ventas)}")
    
    print("\n2. Primeras 3 ventas:")
    for i, v in enumerate(ventas[:3]):
        print(f"   Venta {i}: {v}")
    
    print("\n3. Convirtiendo a DataFrame...")
    df = pd.DataFrame(ventas)
    print(f"   Filas antes de conversión: {len(df)}")
    print(f"   Columnas: {df.columns.tolist()}")
    print(f"   Primeros 3 registros:")
    print(df.head(3))
    
    print("\n4. Verificando columnas necesarias...")
    columnas_necesarias = {'tipo', 'cantidad', 'total', 'fecha'}
    print(f"   Columnas necesarias: {columnas_necesarias}")
    print(f"   ¿Subset presente?: {columnas_necesarias.issubset(df.columns)}")
    
    print("\n5. Convirtiendo tipos de datos...")
    df_copy = df.copy()
    print(f"   Antes - cantidad dtype: {df_copy['cantidad'].dtype}")
    print(f"   Antes - cantidad valores: {df_copy['cantidad'].head(3).tolist()}")
    
    df_copy['cantidad'] = pd.to_numeric(df_copy['cantidad'], errors='coerce')
    df_copy['total'] = pd.to_numeric(df_copy['total'], errors='coerce')
    
    print(f"   Después -cantidad dtype: {df_copy['cantidad'].dtype}")
    print(f"   Después - cantidad valores: {df_copy['cantidad'].head(3).tolist()}")
    print(f"   Nulos introducidos en cantidad: {df_copy['cantidad'].isna().sum()}")
    print(f"   Nulos en total: {df_copy['total'].isna().sum()}")
    
    print("\n6. Codificando tipos...")
    tipos_unicos = df_copy['tipo'].unique()
    print(f"   Tipos únicos: {tipos_unicos}")
    tipo_a_codigo = {tipo: i for i, tipo in enumerate(tipos_unicos)}
    df_copy['tipo_codigo'] = df_copy['tipo'].map(tipo_a_codigo)
    
    print("\n7. Convirtiendo fechas...")
    df_copy['fecha'] = pd.to_datetime(df_copy['fecha'], errors='coerce')
    print(f"   Nulos introducidos en fecha: {df_copy['fecha'].isna().sum()}")
    
    print("\n8. Antes de dropna...")
    print(f"   Filas: {len(df_copy)}")
    print(f"   Nulos totales por columna:")
    print(df_copy.isnull().sum())
    
    print("\n9. Después dropna en ['cantidad', 'total', 'fecha']...")
    df_copy = df_copy.dropna(subset=['cantidad', 'total', 'fecha'])
    print(f"   Filas restantes: {len(df_copy)}")
    
    print("\n10. Extrayendo X, y...")
    df_copy['dia_semana'] = df_copy['fecha'].dt.dayofweek
    X = df_copy[['cantidad', 'tipo_codigo', 'dia_semana']].values
    y = df_copy['total'].values
    print(f"    X shape: {X.shape}")
    print(f"    y shape: {y.shape}")
    print(f"    X[0]: {X[0]}")
    print(f"    y[0]: {y[0]}")
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
