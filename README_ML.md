# 🍫 Nube de Cacao - Analytics Platform

Sistema de análisis de ventas con Machine Learning integrado.

## ✨ Nuevas Características Agregadas

### 1. 🎯 K-Means Clustering
**Ruta**: `/kmeans`

Agrupa automáticamente tus datos de ventas en clusters:
- **Silhouette Score**: Mide la calidad de los clusters (0.5+ es bueno)
- **Davies-Bouldin Index**: Mide separación entre clusters
- **Clusters Óptimos**: Encuentra automáticamente el mejor k
- **Predicción**: Predice el cluster para nuevas ventas

**Parámetros configurables en .env**:
```ini
KMEANS_CLUSTERS=3
KMEANS_INIT=k-means++
KMEANS_N_INIT=10
KMEANS_MAX_ITER=300
```

### 2. 🌳 Árbol de Decisión
**Ruta**: `/arbol-decision`

Dos modelos en uno:

**a) Regresión**: Predice el total de una venta
- R² Score (0-1, preferiblemente >0.7)
- RMSE (Error cuadrático medio)
- Importancia de features

**b) Clasificación**: Clasifica tipos de productos
- Accuracy (% de predicciones correctas)
- Matriz de confusión
- Importancia de features

**Parámetros configurables en .env**:
```ini
DECISION_TREE_MAX_DEPTH=10
DECISION_TREE_MIN_SAMPLES_SPLIT=2
DECISION_TREE_MIN_SAMPLES_LEAF=1
```

## 🔧 Configuración

### Archivo `.env` Requerido

```ini
# MONGODB ATLAS
MONGO_USER=tu_usuario
MONGO_PASSWORD=tu_contraseña
MONGO_CLUSTER=tu_cluster.mongodb.net
MONGO_DB=nube_de_cacao

# FLASK
FLASK_ENV=production
DEBUG=False
SECRET_KEY=tu_clave_secreta

# PRECIOS
PRECIO_AMERICANO=30.0
PRECIO_CAPUCHINO=40.0
PRECIO_LATTE=45.0
PRECIO_ESPRESSO=25.0
PRECIO_MACCHIATO=35.0

# MACHINE LEARNING
KMEANS_CLUSTERS=3
DECISION_TREE_MAX_DEPTH=10

# RESPALDOS
BACKUP_RETAIN_DAYS=30
```

## 📋 Estructura del Proyecto

```
nube-de-cacao/
├── app.py                           # Aplicación Flask principal
├── config.py                        # Configuración centralizada (carga desde .env)
├── db.py                            # Conexión a MongoDB
├── requirements.txt                 # Dependencias
├── .env                             # Variables de entorno ⚙️
│
├── config/
│   └── mongo_spark_conexion.py
│
├── services/                        # Servicios de backend
│   ├── regresion_service.py        # Regresión lineal simple
│   ├── regresion_multiple_service.py  # Regresión múltiple
│   ├── regresion_polinomica_service.py # Regresión polinómica
│   ├── kmeans_service.py            # ✨ K-Means (NUEVO)
│   ├── decision_tree_service.py     # ✨ Árbol de Decisión (NUEVO)
│   ├── auth_service.py
│   ├── perfil_service.py
│   ├── backup_service.py
│   └── ...
│
└── templates/
    ├── regresion.html
    ├── regresion_multiple.html
    ├── kmeans.html                  # ✨ (NUEVO)
    ├── arbol_decision.html          # ✨ (NUEVO)
    └── ...
```

## 🚀 Cómo Empezar

### 1. Instalar Dependencias
```bash
pip install flask pymongo python-dotenv scikit-learn pandas numpy matplotlib openpyxl
```

### 2. Configurar `.env`
```bash
# Edita el archivo .env con tus credenciales MongoDB
nano .env
```

### 3. Ejecutar la Aplicación
```bash
python app.py
```

### 4. Acceder en Navegador
```
http://localhost:5000
```

## 📊 Rutas Disponibles

### Autenticación
- `GET /login` - Página de login
- `POST /login` - Procesar login
- `POST /register` - Crear nueva cuenta
- `GET /logout` - Cerrar sesión

### Dashboard
- `GET /dashboard` - Panel principal
- `GET /perfil` - Perfil de usuario

### Machine Learning
- `GET, POST /regresion` - Regresión simple
- `GET, POST /regresion-multiple` - Regresión múltiple
- `GET, POST /kmeans` - **K-Means Clustering** ✨
- `GET, POST /arbol-decision` - **Árbol de Decisión** ✨

### Respaldos
- `GET /respaldos` - Panel de respaldos
- `POST /respaldos/generar` - Generar respaldo
- `GET /respaldos/centro-descargas` - Centro de descargas

## 🔍 Errores Solucionados

✅ Typo `vventas` → `ventas` (línea 280 app.py)
✅ Variable `collection` no definida → `ventas_col` (línea 260 app.py)
✅ Importaciones faltantes para K-means y Árbol de Decisión
✅ Código duplicado y malformado eliminado
✅ Config.py completamente configurado desde .env

## 📚 Guía de Uso - K-Means

1. Accede a `/kmeans`
2. Se mostrarán tus clusters actuales
3. Usa "Calcular Clusters Óptimos" para encontrar el mejor k
4. Ingresa cantidad y total para predecir el cluster

**Métricas a entender:**
- **Silhouette Score**: >0.5 = Bueno, 0.3-0.5 = Aceptable, <0.3 = Pobre
- **Inertia**: Suma de distancias cuadradas (menor es mejor)
- **Davies-Bouldin**: Menor es mejor (cercano a 0)

## 📚 Guía de Uso - Árbol de Decisión

### Regresión
1. Accede a `/arbol-decision`
2. Ve la pestaña "Árbol de Regresión"
3. Observa R² Score y RMSE
4. Ingresa parámetros en el formulario para predecir

**Métricas:**
- **R² Score**: 1.0 = Perfecto, 0.7+ = Bueno, <0.5 = Malo
- **RMSE**: Menor es mejor
- **Importancia de Features**: Qué variables influyen más

### Clasificación
1. Ve la pestaña "Árbol de Clasificación"
2. Observa Accuracy
3. Comprende qué tipos de productos se clasifican bien

## ⚙️ Personalización

### Cambiar Parámetros ML

Edita `.env`:
```ini
# Para más clusters
KMEANS_CLUSTERS=5

# Para árbol más profundo
DECISION_TREE_MAX_DEPTH=15

# Cambiar precios
PRECIO_AMERICANO=35.0
```

### Entrenar Modelos

Los modelos se entrenan automáticamente al acceder a las rutas. No requieren entrenamiento manual.

## 🐛 Solución de Problemas

### "No hay datos suficientes"
- Necesitas mínimo 5-10 registros de ventas
- Agrega ventas en `/ventas/nueva`

### "Error de conexión MongoDB"
- Verifica credenciales en `.env`
- Comprueba que el cluster esté activo en MongoDB Atlas
- Verifica IP whitelist en MongoDB Atlas

### "ImportError en kmeans_service"
- Asegúrate de tener scikit-learn instalado:
  ```bash
  pip install scikit-learn
  ```

### Modelos dan resultados inconsistentes
- Esto es normal, cada recarga entrena nuevamente
- Los parámetros se pueden ajustar en `.env`

## 📈 Mejoras Futuras

- [ ] Cachear modelos entrenados
- [ ] Gráficos interactivos con Plotly
- [ ] Exportar modelos entrenados
- [ ] Validación cruzada automática
- [ ] Ensambles de modelos

## 📞 Soporte

Si encuentras problemas:
1. Verifica el archivo `.env` está correctamente configurado
2. Revisa la consola para mensajes de error
3. Asegúrate de tener datos suficientes
4. Comprueba la conexión a MongoDB Atlas

## 📄 Licencia

Proyecto Nube de Cacao - 2026

---

**¡Listo para usar!** 🚀 Ejecuta `python app.py` para comenzar.
