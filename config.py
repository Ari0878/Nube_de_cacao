# config.py
# ---------------------- CONFIGURACIÓN ----------------------
import os
from dotenv import load_dotenv

# Cargar variables de entorno (solo una vez)
if not os.getenv("MONGO_USER"):
    load_dotenv()

# ======================== PRECIOS ========================
# Cargar precios desde .env con valores por defecto (EN PESOS MEXICANOS)
PRECIOS = {
    "Americano": float(os.getenv("PRECIO_AMERICANO") or 55.0),
    "Capuchino": float(os.getenv("PRECIO_CAPUCHINO") or 75.0),
    "Latte": float(os.getenv("PRECIO_LATTE") or 85.0),
    "Espresso": float(os.getenv("PRECIO_ESPRESSO") or 45.0),
    "Macchiato": float(os.getenv("PRECIO_MACCHIATO") or 70.0)
}

# ======================== FLASK ========================
FLASK_ENV = os.getenv("FLASK_ENV", "development")
DEBUG = os.getenv("DEBUG", "False") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key")

# ======================== SESIÓN ========================
PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_TIMEOUT", 1800))
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ======================== SEGURIDAD ========================
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", 8))

# ======================== LOGGING ========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")

# ======================== API ========================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))

# ======================== SPARK ========================
SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")
SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "Nube_de_Cacao_Analytics")

# ======================== MACHINE LEARNING ========================
# K-Means
KMEANS_CLUSTERS = int(os.getenv("KMEANS_CLUSTERS", 3))
KMEANS_INIT = os.getenv("KMEANS_INIT", "k-means++")
KMEANS_N_INIT = int(os.getenv("KMEANS_N_INIT", 10))
KMEANS_MAX_ITER = int(os.getenv("KMEANS_MAX_ITER", 300))
KMEANS_RANDOM_STATE = int(os.getenv("KMEANS_RANDOM_STATE", 42))

# Árbol de Decisión
DECISION_TREE_MAX_DEPTH = int(os.getenv("DECISION_TREE_MAX_DEPTH", 10))
DECISION_TREE_MIN_SAMPLES_SPLIT = int(os.getenv("DECISION_TREE_MIN_SAMPLES_SPLIT", 2))
DECISION_TREE_MIN_SAMPLES_LEAF = int(os.getenv("DECISION_TREE_MIN_SAMPLES_LEAF", 1))
DECISION_TREE_RANDOM_STATE = int(os.getenv("DECISION_TREE_RANDOM_STATE", 42))

# Regresión
REGRESSION_TRAIN_SIZE = float(os.getenv("REGRESSION_TRAIN_SIZE", 0.8))
REGRESSION_TEST_SIZE = float(os.getenv("REGRESSION_TEST_SIZE", 0.2))

# ======================== BACKUP ========================
BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "02:00")
BACKUP_FREQUENCY = os.getenv("BACKUP_FREQUENCY", "daily")
BACKUP_RETAIN_DAYS = int(os.getenv("BACKUP_RETAIN_DAYS", 30))
BACKUP_PATH = os.getenv("BACKUP_PATH", "./respaldos")
