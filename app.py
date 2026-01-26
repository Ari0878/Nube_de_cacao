# app.py
from flask import Flask, render_template, request, redirect, session, flash,jsonify
from flask import Flask, render_template, request, redirect, session, flash

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

    session.clear()

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
        

        # IMPORTANTE: Cambiar "email" por "correo" si tu BD usa "correo"
        usuario = verificar_usuario(email, password)
        
        if usuario:  # Ahora es un diccionario, no un booleano
            session.permanent = True
            session["logged_in"] = True
            session["user_email"] = email
            session["user_name"] = usuario.get("nombre", "")
            session["user_role"] = usuario.get("roll", "usuario")  # Nota: "roll" con doble L
            session["user_id"] = usuario.get("_id", "")
            
            nombre_display = session["user_name"] if session["user_name"] else "Usuario"
            flash(f"¡Bienvenido de nuevo, {nombre_display}!", "success")
            
            # Redirigir según el rol
            rol = usuario.get("roll", "usuario")  # Usar "roll" con doble L
            if rol == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/ndc")
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/ndc")
def ndc_home():
    """Página principal para usuarios normales (no admin)"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    # Verificar que no sea admin (por seguridad)
    if session.get("user_role") == "admin":
        return redirect("/dashboard")  # Si es admin, redirigir al dashboard
    
    return render_template("index.html",  # <--- CAMBIO AQUÍ
                         usuario=session.get("user_name"),
                         email=session.get("user_email"))
                         


@app.route("/menu")
def menu():
    """Página del menú"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("menu.html")

@app.route("/about")
def about():
    """Página about"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("about.html")

@app.route("/contact")
def contact():
    """Página de contacto"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("contact.html")

@app.route("/gallery")
def gallery():
    """Página de galería"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("gallery.html")

@app.route("/reservation")
def reservation():
    """Página de reservaciones"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("reservation.html")




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

# Reemplaza la ruta /analisis en app.py con esta versión corregida:

@app.route("/analisis")
def analisis():
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        # Opción 1: Usar la función simplificada
        from services.analisis_service import obtener_resumen_ventas
        resumen = obtener_resumen_ventas()
        
        # Opción 2: O usar la función completa
        # from services.analisis_service import analizar_datos_con_spark
        # _, resumen = analizar_datos_con_spark()
        
        if resumen is None:
            flash("No hay datos suficientes para el análisis.", "warning")
            return render_template("analisis.html", resumen=None)
        
        # Debug: Imprimir en consola para verificar
        print("=" * 50)
        print("RESUMEN DE ANÁLISIS:")
        print(f"Total Productos: {resumen.get('total_productos')}")
        print(f"Total Ingresos: {resumen.get('total_ingresos')}")
        print(f"Precio Promedio: {resumen.get('precio_promedio')}")
        print(f"Top Producto: {resumen.get('top_producto')}")
        print(f"Top Cliente: {resumen.get('top_cliente')}")
        print(f"Ventas por Tipo: {resumen.get('ventas_por_tipo')}")
        print("=" * 50)
        
        return render_template("analisis.html", resumen=resumen)
        
    except Exception as e:
        print(f"Error en ruta /analisis: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error al cargar análisis: {str(e)}", "danger")
        return render_template("analisis.html", resumen=None)

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


# Agregar estas importaciones al inicio de app.py
from flask import send_file
from services.backup_service import (
    generar_backup_completo,
    generar_backup_incremental,
    generar_backup_diferencial,
    generar_excel,
    generar_pdf,
    generar_sql,
    obtener_info_respaldos
    
)

# Agregar estas rutas a tu app.py

@app.route("/respaldos")
def respaldos():
    """Página principal de respaldos"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    # Obtener información de respaldos anteriores
    info = obtener_info_respaldos()
    
    return render_template("respaldos.html", info=info)


@app.route("/respaldos/generar", methods=["POST"])
def generar_respaldo():
    """Genera y descarga un respaldo según los parámetros"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    tipo_backup = request.form.get("tipo_backup", "completo")  # completo, incremental, diferencial
    formato = request.form.get("formato", "excel")  # excel, pdf, sql
    
    try:
        # Generar datos según el tipo de respaldo
        if tipo_backup == "completo":
            ventas, cantidad = generar_backup_completo()
        elif tipo_backup == "incremental":
            ventas, cantidad = generar_backup_incremental()
        elif tipo_backup == "diferencial":
            ventas, cantidad = generar_backup_diferencial()
        else:
            flash("Tipo de respaldo no válido.", "danger")
            return redirect("/respaldos")
        
        # Generar archivo según el formato
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato == "excel":
            archivo = generar_excel(ventas, tipo_backup)
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        elif formato == "pdf":
            archivo = generar_pdf(ventas, tipo_backup)
            mimetype = "application/pdf"
            extension = "pdf"
        elif formato == "sql":
            archivo = generar_sql(ventas, tipo_backup)
            mimetype = "application/sql"
            extension = "sql"
        else:
            flash("Formato no válido.", "danger")
            return redirect("/respaldos")
        
        filename = f"backup_{tipo_backup}_{timestamp}.{extension}"
        
        flash(f"Respaldo {tipo_backup} generado exitosamente: {cantidad} registros.", "success")
        
        return send_file(
            archivo,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"Error al generar respaldo: {str(e)}", "danger")
        return redirect("/respaldos")


@app.route("/respaldos/info")
def info_respaldos():
    """Retorna información de respaldos en JSON (para AJAX)"""
    if not session.get("logged_in"):
        return {"error": "No autorizado"}, 401
    
    info = obtener_info_respaldos()
    return info
# Agregar estas importaciones al inicio de app.py
# from services.auto_backup_service import (
#     cargar_config,
#     guardar_config,
#     cargar_historial,
#     obtener_proximos_respaldos,
#     configurar_scheduler,
#     obtener_estadisticas_historial
# )

# Agregar estas rutas a tu app.py

# @app.route("/respaldos/configuracion")
# def configuracion_respaldos():
#     """Página de configuración de respaldos automáticos"""
#     if not session.get("logged_in"):
#         flash("Debes iniciar sesión para acceder.", "warning")
#         return redirect("/login")
    
#     config = cargar_config()
#     proximos = obtener_proximos_respaldos()
#     historial = cargar_historial()[:10]  # Últimos 10
#     estadisticas = obtener_estadisticas_historial()
    
#     # Formatear fechas del historial para mostrar
#     for item in historial:
#         try:
#             fecha_dt = datetime.fromisoformat(item["fecha"])
#             item["fecha"] = fecha_dt.strftime("%Y-%m-%d %H:%M")
#         except:
#             pass
    
#     return render_template(
#         "configuracion_respaldos.html",
#         config=config,
#         proximos=proximos,
#         historial=historial,
#         estadisticas=estadisticas
#     )


# @app.route("/respaldos/configuracion/guardar", methods=["POST"])
# def guardar_configuracion_respaldos():
#     """Guarda la configuración de respaldos automáticos"""
#     if not session.get("logged_in"):
#         return redirect("/login")
    
#     try:
#         config = {
#             "activo": request.form.get("activo") == "on",
#             "hora": request.form.get("hora", "02:00"),
#             "frecuencia": request.form.get("frecuencia", "diario"),
#             "dia_semana": request.form.get("dia_semana", "monday"),
#             "dia_mes": int(request.form.get("dia_mes", 1)),
#             "formato": request.form.get("formato", "todos"),
#             "limpiar_antiguos": request.form.get("limpiar_antiguos") == "on",
#             "dias_retener": int(request.form.get("dias_retener", 30))
#         }
        
#         guardar_config(config)
#         configurar_scheduler()  # Reconfigurar el scheduler
        
#         flash("Configuración guardada exitosamente.", "success")
        
#     except Exception as e:
#         flash(f"Error al guardar configuración: {str(e)}", "danger")
    
#     return redirect("/respaldos/configuracion")


@app.route("/respaldos/ejecutar-ahora", methods=["POST"])
def ejecutar_respaldo_manual():
    """Ejecuta un respaldo manual y lo descarga inmediatamente"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    formato = request.form.get("formato", "excel")
    
    try:
        from services.backup_service import (
            generar_backup_completo,
            generar_excel,
            generar_pdf,
            generar_sql
        )
        
        # Generar datos
        ventas, cantidad = generar_backup_completo()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archivos = []
        
        # Generar archivos según formato
        if formato == "todos" or formato == "excel":
            archivo_excel = generar_excel(ventas, "manual")
            archivos.append({
                "data": archivo_excel,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "filename": f"backup_manual_{timestamp}.xlsx"
            })
        
        if formato == "todos" or formato == "pdf":
            archivo_pdf = generar_pdf(ventas, "manual")
            archivos.append({
                "data": archivo_pdf,
                "mimetype": "application/pdf",
                "filename": f"backup_manual_{timestamp}.pdf"
            })
        
        if formato == "todos" or formato == "sql":
            archivo_sql = generar_sql(ventas, "manual")
            archivos.append({
                "data": archivo_sql,
                "mimetype": "application/sql",
                "filename": f"backup_manual_{timestamp}.sql"
            })
        
        # Si es un solo archivo, descargarlo directamente
        if len(archivos) == 1:
            from services.auto_backup_service import agregar_historial
            agregar_historial(formato, cantidad, "manual")
            
            flash(f"Respaldo manual generado: {cantidad} registros.", "success")
            
            return send_file(
                archivos[0]["data"],
                mimetype=archivos[0]["mimetype"],
                as_attachment=True,
                download_name=archivos[0]["filename"]
            )
        
        # Si son múltiples archivos, crear un ZIP
        else:
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for archivo in archivos:
                    zip_file.writestr(archivo["filename"], archivo["data"].getvalue())
            
            zip_buffer.seek(0)
            
            from services.auto_backup_service import agregar_historial
            agregar_historial("todos", cantidad, "manual")
            
            flash(f"Respaldo manual generado: {cantidad} registros en {len(archivos)} archivos.", "success")
            
            return send_file(
                zip_buffer,
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"backup_manual_{timestamp}.zip"
            )
    
    except Exception as e:
        flash(f"Error al ejecutar respaldo manual: {str(e)}", "danger")
        return redirect("/respaldos/configuracion")


@app.route("/respaldos/estadisticas")
def estadisticas_respaldos():
    """Retorna estadísticas de respaldos en JSON"""
    if not session.get("logged_in"):
        return {"error": "No autorizado"}, 401
    
    estadisticas = obtener_estadisticas_historial()
    return estadisticas
@app.route("/respaldos/centro-descargas")
def centro_descargas():
    """Centro de descargas - Muestra archivos listos para descargar"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    archivos = listar_archivos_guardados()
    config = cargar_config()
    
    # Contar archivos nuevos (menos de 1 hora)
    pendientes = sum(1 for a in archivos if a.get("es_nuevo", False))
    
    return render_template(
        "centro_descargas.html",
        archivos=archivos,
        pendientes=pendientes,
        dias_retener=config.get("dias_retener", 30)
    )


# Agregar estas importaciones al inicio de app.py
from services.auto_backup_service import (
    cargar_config,
    guardar_config,
    cargar_historial,
    obtener_proximos_respaldos,
    configurar_scheduler,
    obtener_estadisticas_historial,
    listar_archivos_guardados,
    eliminar_archivo,
    obtener_estadisticas_storage,
    ejecutar_respaldo_programado
)

# Agregar estas rutas a tu app.py

@app.route("/respaldos/configuracion")
def configuracion_respaldos():
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    config = cargar_config()
    proximos = obtener_proximos_respaldos()
    historial = cargar_historial()[:10]
    estadisticas = obtener_estadisticas_historial()
    archivos = listar_archivos_guardados()[:10]
    stats_storage = obtener_estadisticas_storage()
    
    for item in historial:
        try:
            fecha_dt = datetime.fromisoformat(item["fecha"])
            item["fecha"] = fecha_dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    return render_template(
        "configuracion_respaldos.html",
        config=config,
        proximos=proximos,
        historial=historial,
        estadisticas=estadisticas,
        archivos=archivos,
        stats_storage=stats_storage
    )



@app.route("/respaldos/configuracion/guardar", methods=["POST"])
def guardar_configuracion_respaldos():
    """Guarda la configuración de respaldos automáticos"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    try:
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
        
        guardar_config(config)
        configurar_scheduler()  # Reconfigurar el scheduler
        
        flash("✅ Configuración guardada exitosamente. Los respaldos se generarán automáticamente.", "success")
        
    except Exception as e:
        flash(f"Error al guardar configuración: {str(e)}", "danger")
    
    return redirect("/respaldos/configuracion")


@app.route("/respaldos/ejecutar-ahora", methods=["POST"])
def ejecutar_respaldo_manual_ahora():
    """
    Ejecuta un respaldo manual inmediatamente y guarda los archivos en el servidor
    """
    if not session.get("logged_in"):
        return redirect("/login")
    
    formato = request.form.get("formato", "excel")
    
    try:
        from services.backup_service import (
            generar_backup_completo,
            generar_excel,
            generar_pdf,
            generar_sql
        )
        from services.auto_backup_service import BACKUPS_STORAGE_DIR, agregar_historial
        
        # Generar datos
        ventas, cantidad = generar_backup_completo()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archivos_generados = []
        
        # Generar y guardar archivos según formato
        if formato == "todos" or formato == "excel":
            archivo_excel = generar_excel(ventas, "manual")
            filename = f"backup_manual_{timestamp}.xlsx"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_excel.getvalue())
            
            archivos_generados.append(filename)
        
        if formato == "todos" or formato == "pdf":
            archivo_pdf = generar_pdf(ventas, "manual")
            filename = f"backup_manual_{timestamp}.pdf"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_pdf.getvalue())
            
            archivos_generados.append(filename)
        
        if formato == "todos" or formato == "sql":
            archivo_sql = generar_sql(ventas, "manual")
            filename = f"backup_manual_{timestamp}.sql"
            filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(archivo_sql.getvalue())
            
            archivos_generados.append(filename)
        
        # Registrar en historial
        agregar_historial(formato, cantidad, archivos_generados, "manual")
        
        flash(f"✅ Respaldo manual ejecutado: {cantidad} registros, {len(archivos_generados)} archivo(s) generado(s).", "success")
        
        # Redirigir al centro de descargas
        return redirect("/respaldos/centro-descargas")
        
    except Exception as e:
        flash(f"❌ Error al ejecutar respaldo manual: {str(e)}", "danger")
        return redirect("/respaldos/configuracion")


@app.route("/respaldos/archivos")
def ver_archivos_respaldos():
    """Página para ver y descargar archivos de respaldos guardados"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    archivos = listar_archivos_guardados()
    stats = obtener_estadisticas_storage()
    
    return render_template(
        "archivos_respaldos.html",
        archivos=archivos,
        stats=stats
    )


@app.route("/respaldos/descargar/<filename>")
def descargar_archivo_respaldo(filename):
    """Descarga un archivo de respaldo específico"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    try:
        from services.auto_backup_service import BACKUPS_STORAGE_DIR
        
        filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
        
        # Validar que el archivo existe y está en la carpeta correcta
        if not os.path.exists(filepath):
            flash("Archivo no encontrado.", "danger")
            return redirect("/respaldos/archivos")
        
        # Determinar mimetype según extensión
        if filename.endswith('.xlsx'):
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.endswith('.pdf'):
            mimetype = "application/pdf"
        elif filename.endswith('.sql'):
            mimetype = "application/sql"
        else:
            mimetype = "application/octet-stream"
        
        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f"Error al descargar archivo: {str(e)}", "danger")
        return redirect("/respaldos/archivos")


@app.route("/respaldos/eliminar/<filename>", methods=["POST"])
def eliminar_archivo_respaldo(filename):
    """Elimina un archivo de respaldo específico"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    success, mensaje = eliminar_archivo(filename)
    
    if success:
        flash(f"✅ {mensaje}", "success")
    else:
        flash(f"❌ {mensaje}", "danger")
    
    return redirect("/respaldos/archivos")


@app.route("/respaldos/limpiar-antiguos", methods=["POST"])
def limpiar_archivos_antiguos():
    """Limpia archivos antiguos manualmente"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    try:
        from services.auto_backup_service import limpiar_backups_antiguos
        
        config = cargar_config()
        dias = config.get("dias_retener", 30)
        
        limpiar_backups_antiguos(dias)
        
        flash(f"✅ Limpieza completada. Archivos más antiguos que {dias} días eliminados.", "success")
    
    except Exception as e:
        flash(f"❌ Error al limpiar archivos: {str(e)}", "danger")
    
    return redirect("/respaldos/archivos")


@app.route("/respaldos/forzar-ejecucion", methods=["POST"])
def forzar_ejecucion_respaldo():
    """Fuerza la ejecución del respaldo automático inmediatamente (simula el scheduler)"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    try:
        ejecutar_respaldo_programado()
        flash("✅ Respaldo automático ejecutado. Ve al Centro de Descargas para descargar los archivos.", "success")
        return redirect("/respaldos/centro-descargas")
    except Exception as e:
        flash(f"❌ Error al forzar ejecución: {str(e)}", "danger")
        return redirect("/respaldos/configuracion")
    
# ======================== REGRESIÓN POLINÓMICA ========================
# @app.route("/regresion-polinomica", methods=["GET", "POST"])
# def regresion_polinomica():
#     if not session.get("logged_in"):
#         return redirect("/login")
    
#     grado = 2  # grado por defecto
    
#     if request.method == "POST":
#         try:
#             grado = int(request.form.get("grado", 2))
#             grado = max(1, min(grado, 10))  # limitar entre 1 y 10
#         except:
#             grado = 2
    
#     modelo = entrenar_modelo_polinomico(grado)
    
#     return render_template("regresion_polinomica.html", modelo=modelo, grado=grado)
# ========== RUTAS API PARA CONFIGURACIÓN DE RESPALDOS ==========

@app.route('/respaldos/api/estadisticas', methods=['GET'])
def api_estadisticas():
    """API para obtener estadísticas en tiempo real"""
    from services.auto_backup_service import obtener_estadisticas_historial, obtener_estadisticas_storage
    
    estadisticas_historial = obtener_estadisticas_historial()
    estadisticas_storage = obtener_estadisticas_storage()
    
    return jsonify({
        "total_respaldos": estadisticas_historial.get("total_respaldos", 0),
        "exitosos": estadisticas_historial.get("exitosos", 0),
        "total_archivos": estadisticas_storage.get("total_archivos", 0),
        "tamaño_total_mb": estadisticas_storage.get("tamaño_total_mb", 0)
    })


@app.route('/respaldos/api/proximos-respaldos', methods=['GET'])
def api_proximos_respaldos():
    """API para obtener próximos respaldos programados"""
    from services.auto_backup_service import obtener_proximos_respaldos
    
    proximos = obtener_proximos_respaldos()
    return jsonify(proximos)


@app.route('/respaldos/api/historial-reciente', methods=['GET'])
def api_historial_reciente():
    """API para obtener historial reciente"""
    from services.auto_backup_service import cargar_historial
    
    historial = cargar_historial()
    # Retornar solo los últimos 10
    return jsonify(historial[:10])


@app.route('/respaldos/api/archivos-recientes', methods=['GET'])
def api_archivos_recientes():
    """API para obtener archivos recientes"""
    from services.auto_backup_service import listar_archivos_guardados
    
    archivos = listar_archivos_guardados()
    # Retornar solo los primeros 5
    return jsonify(archivos[:5])


@app.route('/respaldos/api/config-email', methods=['GET'])
def get_config_email():
    """Obtiene la configuración de email (sin mostrar credenciales)"""
    from services.email_service import cargar_config_email
    
    config = cargar_config_email()
    
    # No enviar credenciales sensibles al frontend
    return jsonify({
        "activo": config.get("activo", False),
        "emails_destino": config.get("emails_destino", []),
        "incluir_adjuntos": config.get("incluir_adjuntos", True)
    })


@app.route('/respaldos/api/config-email/guardar', methods=['POST'])
def guardar_config_email():
    """Guarda la configuración de email"""
    from services.email_service import guardar_config_email, cargar_config_email
    
    try:
        data = request.get_json()
        
        # Cargar config actual para mantener credenciales
        config = cargar_config_email()
        
        # Actualizar solo los campos permitidos
        config["activo"] = data.get("activo", False)
        config["emails_destino"] = data.get("emails_destino", [])
        config["incluir_adjuntos"] = data.get("incluir_adjuntos", True)
        
        # Guardar
        guardar_config_email(config)
        
        return jsonify({
            "success": True,
            "message": "Configuración de correo guardada exitosamente"
        })
    
    except Exception as e:
        import traceback
        print(f"Error guardando config email: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"Error al guardar configuración: {str(e)}"
        }), 500


@app.route('/respaldos/api/email/prueba', methods=['POST'])
def enviar_prueba_email():
    """Envía un correo de prueba"""
    from services.email_service import enviar_correo_prueba, cargar_config_email, guardar_config_email
    
    try:
        data = request.get_json()
        emails_destino = data.get("emails_destino", [])
        
        if not emails_destino:
            return jsonify({
                "success": False,
                "message": "No se especificaron correos de destino"
            }), 400
        
        # Guardar temporalmente los emails para la prueba
        config = cargar_config_email()
        
        # Validar que las credenciales estén configuradas
        if not config.get("email_from") or not config.get("email_password"):
            return jsonify({
                "success": False,
                "message": "Las credenciales de correo no están configuradas correctamente en el servidor"
            }), 500
        
        config["emails_destino"] = emails_destino
        config["activo"] = True
        guardar_config_email(config)
        
        # Enviar correo de prueba
        success, mensaje = enviar_correo_prueba()
        
        if success:
            return jsonify({
                "success": True,
                "message": mensaje
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Error: {mensaje}"
            }), 500
    
    except Exception as e:
        import traceback
        error_detallado = traceback.format_exc()
        print(f"Error detallado en prueba de email:\n{error_detallado}")
        
        return jsonify({
            "success": False,
            "message": f"Error al enviar correo: {str(e)}"
        }), 500


@app.route('/respaldos/ejecutar-prueba', methods=['POST'])
def ejecutar_prueba_respaldo():
    """Ejecuta un respaldo de prueba y lo envía por correo si está configurado"""
    from services.auto_backup_service import ejecutar_respaldo_prueba
    
    try:
        success, mensaje = ejecutar_respaldo_prueba()
        
        return jsonify({
            "success": success,
            "message": mensaje
        })
    
    except Exception as e:
        import traceback
        print(f"Error en prueba de respaldo: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
