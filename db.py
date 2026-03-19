# db.py
# ---------------------- CONEXIÓN A MYSQL ----------------------
import mysql.connector

conn = None
cursor = None
ventas_table = None
usuarios_table = None


def conectar():
    global conn, cursor, ventas_table, usuarios_table
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="cafeteria_db",
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor(dictionary=True)
        ventas_table = "ventas"
        usuarios_table = "usuarios"

        conn.ping(reconnect=True)
        print("Conectado a MySQL cafeterÃ­a_db correctamente")

    except mysql.connector.Error as e:
        # Si la base no existe, conectamos al servidor sin DB para permitir creaciÃ³n/uso.
        if e.errno == 1049:
            print("Base de datos cafeteria_db no existe. Conectando sin base para restaurar.")
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    auth_plugin='mysql_native_password'
                )
                cursor = conn.cursor(dictionary=True)
                ventas_table = "ventas"
                usuarios_table = "usuarios"
                conn.ping(reconnect=True)
            except Exception as e2:
                print(f"CRITICAL: No se pudo conectar a MySQL sin DB: {e2}")
                conn = None
                cursor = None
                ventas_table = None
                usuarios_table = None
        else:
            print(f"CRITICAL: No se pudo conectar a MySQL: {e}")
            conn = None
            cursor = None
            ventas_table = None
            usuarios_table = None

    return conn, cursor


def get_connection():
    global conn
    if conn is None:
        conectar()
        return conn

    try:
        conn.ping(reconnect=True)
    except Exception as e:
        print(f"Advertencia: conexión perdida o cerrada, reconectando... {e}")
        conectar()

    return conn


def get_cursor():
    global cursor
    get_connection()
    return cursor


# Inicializar al importar
conectar()