from flask import Flask, render_template, request, redirect, session, flash
from flask import send_file
from services.auth_service import verificar_usuario, registrar_usuario
from services.ventas_service import cargar_y_analizar_ventas
from services.analisis_service import analizar_datos_con_spark
from services.regresion_service import entrenar_modelo_regresion, predecir_total
from services.regresion_multiple_service import entrenar_modelo_multiple, predecir_total_venta
from services.regresion_polinomica_service import entrenar_modelo_polinomico
from services.perfil_service import (
    actualizar_datos_usuario, cambiar_password_usuario, 
    guardar_avatar, obtener_datos_usuario, guardar_preferencias
)
from config import PRECIOS
from db import collection
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Por favor ingresa correo y contraseña.", "danger")
            return redirect("/login")
        
        if verificar_usuario(email, password):
            session.permanent = True
            session["logged_in"] = True
            session["user_email"] = email
            flash(f"Bienvenido de nuevo!", "success")
            return redirect("/dashboard")
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect("/login")
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("reg_email", "").strip()
    pwd = request.form.get("reg_password", "")
    conf = request.form.get("reg_confirm", "")
    
    if not email or not pwd or not conf:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect("/login")
    
    if pwd != conf:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect("/login")
    
    success, msg = registrar_usuario(email, pwd)
    if success:
        flash(msg + " Ahora puedes iniciar sesión.", "success")
        return redirect("/login")
    else:
        flash(msg, "danger")
        return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "success")
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    user_email = session.get("user_email")
    datos = obtener_datos_usuario(user_email)
    return render_template("dashboard.html", usuario=datos)

@app.route("/ventas/resumen")
def ventas_dashboard():
    df, resumen = cargar_y_analizar_ventas()
    return render_template("ventas.html", df=df, resumen=resumen)

@app.route("/analisis")
def analisis():
    df, _ = cargar_y_analizar_ventas()
    _, resumen = analizar_datos_con_spark(df)
    return render_template("analisis.html", resumen=resumen)

@app.route("/regresion", methods=["GET", "POST"])
def regresion():
    if not session.get("logged_in"):
        return redirect("/login")
    
    modelo = entrenar_modelo_regresion()
    prediccion = None
    
    if request.method == "POST" and modelo:
        cantidad = float(request.form.get("cantidad", 0))
        prediccion = predecir_total(cantidad, modelo)
    
    return render_template("regresion.html", modelo=modelo, prediccion=prediccion)

@app.route("/ventas/nueva", methods=["GET", "POST"])
def registrar_venta():
    if request.method == "POST":
        cliente = request.form["cliente"]
        tipo = request.form["tipo"]
        cantidad = int(request.form["cantidad"])
        total = PRECIOS[tipo] * cantidad
        venta = {
            "cliente": cliente,
            "tipo": tipo,
            "cantidad": cantidad,
            "total": total,
            "fecha": datetime.now()
        }
        collection.insert_one(venta)
        return render_template("registrar_venta.html", precios=PRECIOS, mensaje="Venta registrada correctamente.")
    return render_template("registrar_venta.html", precios=PRECIOS)

@app.route("/ventas/historial")
def historial():
    ventas = list(collection.find().sort("fecha", -1))
    for v in ventas:
        v["_id"] = str(v["_id"])
        v["fecha"] = v["fecha"].strftime("%Y-%m-%d %H:%M:%S")
    return render_template("historial.html", ventas=ventas)

@app.route("/perfil")
def perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_email = session.get("user_email")
    datos = obtener_datos_usuario(user_email)
    return render_template("perfil.html", usuario=datos)

@app.route("/perfil/actualizar", methods=["POST"])
def actualizar_perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_email = session.get("user_email")
    nombre = request.form.get("nombre")
    nuevo_email = request.form.get("email")
    telefono = request.form.get("telefono")
    success, mensaje = actualizar_datos_usuario(user_email, nombre, nuevo_email, telefono)
    if success:
        if user_email != nuevo_email:
            session["user_email"] = nuevo_email
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil#info")

@app.route("/perfil/cambiar-foto", methods=["POST"])
def cambiar_foto_perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_email = session.get("user_email")
    if 'avatar' not in request.files:
        flash("No se seleccionó ningún archivo.", "warning")
        return redirect("/perfil")
    file = request.files['avatar']
    success, mensaje = guardar_avatar(user_email, file)
    if success:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil")

@app.route("/perfil/cambiar-password", methods=["POST"])
def cambiar_password():
    if not session.get("logged_in"):
        return redirect("/login")
    user_email = session.get("user_email")
    password_actual = request.form.get("password_actual")
    password_nueva = request.form.get("password_nueva")
    password_confirmar = request.form.get("password_confirmar")
    if password_nueva != password_confirmar:
        flash("Las contraseñas nuevas no coinciden.", "danger")
        return redirect("/perfil#security")
    success, mensaje = cambiar_password_usuario(user_email, password_actual, password_nueva)
    if success:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil#security")

@app.route("/perfil/preferencias", methods=["POST"])
def guardar_preferencias_usuario():
    if not session.get("logged_in"):
        return redirect("/login")
    user_email = session.get("user_email")
    tema = request.form.get("tema_preferido")
    idioma = request.form.get("idioma", "es")
    
    # Guardar idioma en sesión para cambio inmediato
    session['idioma'] = idioma
    
    success, mensaje = guardar_preferencias(user_email, tema, idioma)
    if success:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil#settings")

# ======================== REGRESIÓN MÚLTIPLE ========================
@app.route("/regresion-multiple", methods=["GET", "POST"])
def regresion_multiple():
    if not session.get("logged_in"):
        return redirect("/login")
    
    modelo = entrenar_modelo_multiple()
    prediccion = None
    
    if request.method == "POST" and modelo and request.form.get("cantidad"):
        try:
            cantidad = int(request.form.get("cantidad"))
            tipo_producto = request.form.get("tipo")
            dia_semana = int(request.form.get("dia_semana"))
            prediccion = predecir_total_venta(cantidad, tipo_producto, dia_semana, modelo)
        except:
            pass
    
    return render_template("regresion_multiple.html", modelo=modelo, prediccion=prediccion)

# ======================== REGRESIÓN POLINÓMICA ========================
@app.route("/regresion-polinomica", methods=["GET", "POST"])
def regresion_polinomica():
    if not session.get("logged_in"):
        return redirect("/login")
    
    grado = 2  # grado por defecto
    
    if request.method == "POST":
        try:
            grado = int(request.form.get("grado", 2))
            grado = max(1, min(grado, 10))  # limitar entre 1 y 10
        except:
            grado = 2
    
    modelo = entrenar_modelo_polinomico(grado)
    
    return render_template("regresion_polinomica.html", modelo=modelo, grado=grado)
from services.backup_service import (
    exportar_excel, 
    exportar_pdf, 
    exportar_sql, 
    obtener_estadisticas_backup
)

# Agregar estas rutas antes del if __name__ == "__main__":

# ======================== RESPALDOS ========================
@app.route("/respaldos")
def respaldos():
    """Página de respaldos y exportación de datos"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    estadisticas = obtener_estadisticas_backup()
    return render_template("respaldos.html", stats=estadisticas)


@app.route("/respaldos/descargar/excel")
def descargar_excel():
    """Descarga el respaldo en formato Excel"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        archivo = exportar_excel()
        
        if archivo is None:
            flash("No hay datos para exportar.", "warning")
            return redirect("/respaldos")
        
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"ventas_nube_cacao_{fecha_actual}.xlsx"
        
        return send_file(
            archivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        flash(f"Error al exportar a Excel: {str(e)}", "danger")
        return redirect("/respaldos")


@app.route("/respaldos/descargar/pdf")
def descargar_pdf():
    """Descarga el respaldo en formato PDF"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        archivo = exportar_pdf()
        
        if archivo is None:
            flash("No hay datos para exportar.", "warning")
            return redirect("/respaldos")
        
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"ventas_nube_cacao_{fecha_actual}.pdf"
        
        return send_file(
            archivo,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        flash(f"Error al exportar a PDF: {str(e)}", "danger")
        return redirect("/respaldos")


@app.route("/respaldos/descargar/sql")
def descargar_sql():
    """Descarga el respaldo en formato SQL"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        archivo = exportar_sql()
        
        if archivo is None:
            flash("No hay datos para exportar.", "warning")
            return redirect("/respaldos")
        
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"ventas_nube_cacao_{fecha_actual}.sql"
        
        return send_file(
            archivo,
            mimetype='text/plain',
            as_attachment=True,
            download_name=nombre_archivo
        )
    except Exception as e:
        flash(f"Error al exportar a SQL: {str(e)}", "danger")
        return redirect("/respaldos")
from services.scheduler_service import (
    iniciar_scheduler,
    detener_scheduler,
    guardar_configuracion,
    cargar_configuracion,
    obtener_proximos_respaldos,
    obtener_historial_respaldos,
    realizar_respaldo_automatico
)

# Agregar estas rutas antes del if __name__ == "__main__":

# ======================== CONFIGURACIÓN DE RESPALDOS AUTOMÁTICOS ========================
@app.route("/respaldos/configuracion", methods=["GET"])
def configuracion_respaldos():
    """Página de configuración de respaldos automáticos"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    config = cargar_configuracion()
    proximos = obtener_proximos_respaldos()
    historial = obtener_historial_respaldos(limite=20)
    
    return render_template(
        "configuracion_respaldos.html",
        config=config,
        proximos=proximos,
        historial=historial
    )


@app.route("/respaldos/configuracion/guardar", methods=["POST"])
def guardar_configuracion_respaldos():
    """Guarda la configuración de respaldos automáticos"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        # Obtener datos del formulario
        config = {
            "activo": request.form.get("activo") == "on",
            "hora": request.form.get("hora", "02:00"),
            "frecuencia": request.form.get("frecuencia", "diario"),
            "dia_semana": request.form.get("dia_semana", "monday"),
            "dia_mes": int(request.form.get("dia_mes", 1)),
            "formato": request.form.get("formato", "todos"),
            "limpiar_antiguos": request.form.get("limpiar_antiguos") == "on",
            "dias_retener": int(request.form.get("dias_retener", 30))
        }
        
        # Guardar en base de datos
        if guardar_configuracion(config):
            # Reiniciar scheduler con nueva configuración
            detener_scheduler()
            if config["activo"]:
                iniciar_scheduler(config)
            
            flash("Configuración de respaldos guardada exitosamente.", "success")
        else:
            flash("Error al guardar la configuración.", "danger")
    
    except Exception as e:
        flash(f"Error al guardar configuración: {str(e)}", "danger")
    
    return redirect("/respaldos/configuracion")


@app.route("/respaldos/ejecutar-ahora", methods=["POST"])
def ejecutar_respaldo_manual():
    """Ejecuta un respaldo manual inmediatamente"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        formato = request.form.get("formato", "todos")
        realizar_respaldo_automatico(formato=formato)
        flash(f"Respaldo {formato} ejecutado exitosamente. Revisa la carpeta 'backups_automaticos'.", "success")
    except Exception as e:
        flash(f"Error al ejecutar respaldo: {str(e)}", "danger")
    
    return redirect("/respaldos/configuracion")


# ======================== INICIAR SCHEDULER AL ARRANCAR LA APP ========================
# Agregar esto ANTES del if __name__ == "__main__":

# Cargar configuración e iniciar scheduler al arrancar
config_inicial = cargar_configuracion()
if config_inicial.get("activo", False):
    iniciar_scheduler(config_inicial)
    print("✅ Respaldos automáticos activados")
if __name__ == "__main__":
    app.run(debug=True, port=5001)
