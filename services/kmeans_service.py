import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from db import ventas_col
import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

def obtener_datos_para_kmeans():
    """Obtiene datos de ventas para clustering K-means"""
    try:
        ventas = list(ventas_col.find(
            {},
            {'_id': 0, 'cantidad': 1, 'total': 1, 'fecha': 1}
        ).limit(500))
        
        if len(ventas) < 5:
            return None, None, None
        
        df = pd.DataFrame(ventas)
        
        # ✅ CONVERTIR TIPOS DE DATOS
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')
        df['total'] = pd.to_numeric(df['total'], errors='coerce')
        
        # Validar columnas necesarias
        if not all(col in df.columns for col in ['cantidad', 'total']):
            return None, None, None
        
        # Eliminar valores nulos
        df = df.dropna(subset=['cantidad', 'total'])
        df = df[(df['cantidad'] > 0) & (df['total'] > 0)]
        
        if len(df) < 5:
            return None, None, None
        
        # Crear características para clustering
        df['precio_unitario'] = df['total'] / df['cantidad']
        
        # Normalizar datos
        X = df[['cantidad', 'total', 'precio_unitario']].values.astype(np.float32)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, df, scaler
    
    except Exception as e:
        print(f"Error obtener_datos_para_kmeans: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def entrenar_kmeans(n_clusters=None):
    """Entrena modelo K-means con datos de ventas"""
    try:
        X_scaled, df, scaler = obtener_datos_para_kmeans()
        
        if X_scaled is None:
            return None
        
        # Determinar número óptimo de clusters si no se proporciona
        if n_clusters is None:
            n_clusters = int(os.getenv('KMEANS_CLUSTERS', 3))
        
        # Entrenar modelo
        kmeans = KMeans(
            n_clusters=n_clusters,
            init=os.getenv('KMEANS_INIT', 'k-means++'),
            n_init=int(os.getenv('KMEANS_N_INIT', 10)),
            max_iter=int(os.getenv('KMEANS_MAX_ITER', 300)),
            random_state=int(os.getenv('KMEANS_RANDOM_STATE', 42))
        )
        
        labels = kmeans.fit_predict(X_scaled)
        
        # Métricas de evaluación
        silhouette = silhouette_score(X_scaled, labels)
        davies_bouldin = davies_bouldin_score(X_scaled, labels)
        inertia = kmeans.inertia_
        
        # Diagnosticar calidad del clustering
        if silhouette > 0.5:
            diagnostico = "Excelente: Clusters bien separados y cohesivos"
            color = "success"
        elif silhouette > 0.3:
            diagnostico = "Bueno: Clusters razonablemente bien definidos"
            color = "info"
        elif silhouette > 0.0:
            diagnostico = "Aceptable: Clusters débiles pero presentes"
            color = "warning"
        else:
            diagnostico = "Pobre: Estructura de clusters no clara"
            color = "danger"
        
        # Añadir labels al dataframe
        df['cluster'] = labels
        
        # Estadísticas por cluster
        cluster_stats = []
        for i in range(n_clusters):
            cluster_data = df[df['cluster'] == i]
            stats = {
                'cluster_id': int(i),
                'cantidad_registros': int(len(cluster_data)),
                'cantidad_promedio': float(cluster_data['cantidad'].mean()),
                'total_promedio': float(cluster_data['total'].mean()),
                'precio_unitario_promedio': float(cluster_data['precio_unitario'].mean()),
                'cantidad_std': float(cluster_data['cantidad'].std()),
                'total_std': float(cluster_data['total'].std())
            }
            cluster_stats.append(stats)
        
        # Limitar puntos para visualización
        num_puntos = min(200, len(X_scaled))
        indices = np.random.choice(len(X_scaled), num_puntos, replace=False)
        
        return {
            'n_clusters': int(n_clusters),
            'silhouette_score': float(silhouette),
            'davies_bouldin_score': float(davies_bouldin),
            'inertia': float(inertia),
            'diagnostico': diagnostico,
            'color_diagnostico': color,
            'cluster_stats': cluster_stats,
            'centroids': kmeans.cluster_centers_.tolist(),
            'labels': labels[indices].tolist(),
            'X_data': X_scaled[indices, 0].tolist(),  # cantidad
            'y_data': X_scaled[indices, 1].tolist(),  # total
            'num_datos_total': len(X_scaled),
            'num_datos_visualizados': num_puntos
        }
    
    except Exception as e:
        print(f"Error entrenar_kmeans: {e}")
        import traceback
        traceback.print_exc()
        return None


def calcular_clusters_optimos(max_k=10):
    """Calcula el número óptimo de clusters usando el método del codo"""
    try:
        X_scaled, _, _ = obtener_datos_para_kmeans()
        
        if X_scaled is None or len(X_scaled) < 5:
            return None
        
        inertias = []
        silhouettes = []
        K_range = range(2, min(max_k + 1, len(X_scaled)))
        
        for k in K_range:
            kmeans = KMeans(
                n_clusters=k,
                init='k-means++',
                n_init=10,
                max_iter=300,
                random_state=42,
                n_jobs=-1
            )
            labels = kmeans.fit_predict(X_scaled)
            inertias.append(kmeans.inertia_)
            silhouettes.append(silhouette_score(X_scaled, labels))
        
        # Encontrar k óptimo (máxima silueta)
        k_optimo = K_range[np.argmax(silhouettes)]
        
        return {
            'k_range': list(K_range),
            'inertias': inertias,
            'silhouettes': silhouettes,
            'k_optimo': int(k_optimo),
            'silhouette_optimo': float(silhouettes[np.argmax(silhouettes)])
        }
    
    except Exception as e:
        print(f"Error calcular_clusters_optimos: {e}")
        return None


def predecir_cluster(cantidad, total):
    """Predice a qué cluster pertenece una venta nueva"""
    try:
        X_scaled, df, scaler = obtener_datos_para_kmeans()
        
        if X_scaled is None:
            return None
        
        # Entrenar modelo
        kmeans = KMeans(
            n_clusters=int(os.getenv('KMEANS_CLUSTERS', 3)),
            init='k-means++',
            n_init=10,
            max_iter=300,
            random_state=42
        )
        kmeans.fit(X_scaled)
        
        # Preparar datos nuevos
        precio_unitario = total / cantidad if cantidad > 0 else 0
        X_nuevo = np.array([[cantidad, total, precio_unitario]])
        X_nuevo_scaled = scaler.transform(X_nuevo)
        
        # Predecir cluster
        cluster = kmeans.predict(X_nuevo_scaled)[0]
        distancia = kmeans.transform(X_nuevo_scaled)[0][cluster]
        
        return {
            'cluster': int(cluster),
            'distancia_al_centroide': float(distancia),
            'cantidad': float(cantidad),
            'total': float(total),
            'precio_unitario': float(precio_unitario)
        }
    
    except Exception as e:
        print(f"Error predecir_cluster: {e}")
        return None
