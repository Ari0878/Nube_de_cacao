# app.py
from flask import Flask, render_template, request, redirect, session, flash, jsonify, send_file, get_flashed_messages
from functools import wraps

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
# CAMBIO IMPORTANTE: Ya no importamos 'collection' porque no existe
from db import conn, cursor, ventas_table, usuarios_table
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"


def login_required(func):
    """Decorador que exige estar autenticado."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Debes iniciar sesión para acceder.", "warning")
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """Decorador que exige ser administrador."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Debes iniciar sesión para acceder.", "warning")
            return redirect("/login")
        if session.get("user_role") != "admin":
            flash("No tienes permisos para acceder a esta sección.", "danger")
            return redirect("/dashboard")
        return func(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    session.clear()
    if session.get("logged_in"):
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Aceptamos tanto 'correo' como 'email' desde el formulario, para evitar desajustes entre frontend/back
        correo = request.form.get("correo", "").strip() or request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not correo or not password:
            flash("Por favor ingresa correo y contraseña.", "danger")
            return redirect("/login")
        
        usuario = verificar_usuario(correo, password)
        
        if usuario:  # Ahora es un diccionario, no un booleano
            session.permanent = True
            session["logged_in"] = True
            session["user_correo"] = correo
            session["user_name"] = usuario.get("nombre", "")
            session["user_role"] = usuario.get("rol", "usuario")  # Nota: "roll" con doble L
            session["user_id"] = usuario.get("id", "")  # Cambiado de _id a id para MySQL
            
            nombre_display = session["user_name"] if session["user_name"] else "Usuario"
            flash(f"¡Bienvenido de nuevo, {nombre_display}!", "success")
            
            # Redirigir según el rol
            rol = usuario.get("rol", "usuario")
            if rol == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/ndc")
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect("/login")
    
    # Limpiar mensajes antiguos (evita que errores de restauración aparezcan en la pantalla de login)
    get_flashed_messages()
    return render_template("login.html")

@app.route("/ndc")
@login_required
def ndc_home():
    """Redirige al dashboard (usuarios normales)."""
    return redirect("/dashboard")

@app.route("/menu")
@login_required
def menu():
    """Página del menú"""
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("menu.html")

@app.route("/about")
@login_required
def about():
    """Página about"""
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("about.html")

@app.route("/contact")
@login_required
def contact():
    """Página de contacto"""
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("contact.html")

@app.route("/gallery")
@login_required
def gallery():
    """Página de galería"""
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("gallery.html")

@app.route("/reservation")
@login_required
def reservation():
    """Página de reservaciones"""
    if session.get("user_role") == "admin":
        return redirect("/dashboard")
    
    return render_template("reservation.html")

@app.route("/register", methods=["POST"])
def register():
    correo = request.form.get("reg_email", "").strip()
    pwd = request.form.get("reg_password", "")
    conf = request.form.get("reg_confirm", "")
    
    if not correo or not pwd or not conf:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect("/login")
    
    if pwd != conf:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect("/login")
    
    success, msg = registrar_usuario(correo, pwd)
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
@login_required
def dashboard():
    user_correo = session.get("user_correo")
    datos = obtener_datos_usuario(user_correo)
    return render_template(
        "dashboard.html",
        usuario=datos,
        user_role=session.get("user_role", "usuario")
    )

@app.route("/admin/usuarios")
@admin_required
def admin_usuarios():
    """Lista y permite cambiar el rol de los usuarios."""
    from services.auth_service import listar_usuarios

    usuarios = listar_usuarios()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@app.route("/admin/usuarios/rol", methods=["POST"])
@admin_required
def admin_cambiar_rol():
    correo = request.form.get("correo")
    nuevo_rol = request.form.get("rol")

    if not correo or not nuevo_rol:
        flash("Correo y rol son requeridos.", "danger")
        return redirect("/admin/usuarios")

    from services.auth_service import cambiar_rol_usuario
    success, mensaje = cambiar_rol_usuario(correo, nuevo_rol)

    flash(mensaje, "success" if success else "danger")
    return redirect("/admin/usuarios")


@app.route("/ventas/resumen")
def ventas_dashboard():
    df, resumen = cargar_y_analizar_ventas()
    return render_template("ventas.html", df=df, resumen=resumen)

@app.route("/analisis")
def analisis():
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    try:
        from services.analisis_service import obtener_resumen_ventas
        resumen = obtener_resumen_ventas()
        
        if resumen is None:
            flash("No hay datos suficientes para el análisis.", "warning")
            return render_template("analisis.html", resumen=None)
        
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
        
        # CAMBIO: Usar la función guardar_venta en lugar de collection.insert_one
        from services.ventas_service import guardar_venta
        guardar_venta(venta)
        
        return render_template("registrar_venta.html", precios=PRECIOS, mensaje="Venta registrada correctamente.")
    return render_template("registrar_venta.html", precios=PRECIOS)

@app.route("/ventas/historial")
def historial():
    # CAMBIO: Usar cursor en lugar de collection.find()
    if cursor:
        cursor.execute(f"SELECT id, cliente, tipo, cantidad, total, fecha FROM {ventas_table} ORDER BY fecha DESC")
        ventas = cursor.fetchall()
        
        # Formatear fechas para mostrar
        for v in ventas:
            if v.get("fecha"):
                v["fecha"] = v["fecha"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(v["fecha"], "strftime") else str(v["fecha"])
    else:
        ventas = []
    
    return render_template("historial.html", ventas=ventas)

@app.route("/perfil")
def perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_correo = session.get("user_correo")
    datos = obtener_datos_usuario(user_correo)
    return render_template("perfil.html", usuario=datos)

@app.route("/perfil/actualizar", methods=["POST"])
def actualizar_perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_correo = session.get("user_correo")
    nombre = request.form.get("nombre")
    nuevo_correo = request.form.get("correo")
    telefono = request.form.get("telefono")
    success, mensaje = actualizar_datos_usuario(user_correo, nombre, nuevo_correo, telefono)
    if success:
        if user_correo != nuevo_correo:
            session["user_correo"] = nuevo_correo
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil#info")

@app.route("/perfil/cambiar-foto", methods=["POST"])
def cambiar_foto_perfil():
    if not session.get("logged_in"):
        return redirect("/login")
    user_correo = session.get("user_correo")
    if 'avatar' not in request.files:
        flash("No se seleccionó ningún archivo.", "warning")
        return redirect("/perfil")
    file = request.files['avatar']
    success, mensaje = guardar_avatar(user_correo, file)
    if success:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil")

@app.route("/perfil/cambiar-password", methods=["POST"])
def cambiar_password():
    if not session.get("logged_in"):
        return redirect("/login")
    user_correo = session.get("user_correo")
    password_actual = request.form.get("password_actual")
    password_nueva = request.form.get("password_nueva")
    password_confirmar = request.form.get("password_confirmar")
    if password_nueva != password_confirmar:
        flash("Las contraseñas nuevas no coinciden.", "danger")
        return redirect("/perfil#security")
    success, mensaje = cambiar_password_usuario(user_correo, password_actual, password_nueva)
    if success:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect("/perfil#security")

@app.route("/perfil/preferencias", methods=["POST"])
def guardar_preferencias_usuario():
    if not session.get("logged_in"):
        return redirect("/login")
    user_correo = session.get("user_correo")
    tema = request.form.get("tema_preferido")
    idioma = request.form.get("idioma", "es")
    
    # Guardar idioma en sesión para cambio inmediato
    session['idioma'] = idioma
    
    success, mensaje = guardar_preferencias(user_correo, tema, idioma)
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

# ======================== RESPALDOS ========================
from services.backup_service import (
    generar_backup_completo,
    generar_backup_incremental,
    generar_backup_diferencial,
    generar_excel,
    generar_pdf,
    generar_sql,
    obtener_info_respaldos
)

@app.route("/respaldos")
@admin_required
def respaldos():
    """Página principal de respaldos"""
    info = obtener_info_respaldos()
    return render_template("respaldos.html", info=info)

@app.route("/respaldos/generar", methods=["POST"])
@admin_required
def generar_respaldo():
    """Genera y descarga un respaldo según los parámetros"""
    
    tipo_backup = request.form.get("tipo_backup", "completo")
    formato = request.form.get("formato", "excel")
    
    try:
        if tipo_backup == "completo":
            ventas, cantidad = generar_backup_completo()
        elif tipo_backup == "incremental":
            ventas, cantidad = generar_backup_incremental()
        elif tipo_backup == "diferencial":
            ventas, cantidad = generar_backup_diferencial()
        else:
            flash("Tipo de respaldo no válido.", "danger")
            return redirect("/respaldos")
        
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
@admin_required
def info_respaldos():
    """Retorna información de respaldos en JSON (para AJAX)"""
    info = obtener_info_respaldos()
    return info

# ======================== CONFIGURACIÓN DE RESPALDOS AUTOMÁTICOS ========================
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
    ejecutar_respaldo_programado,
    BACKUPS_STORAGE_DIR
)

@app.route("/respaldos/configuracion")
@admin_required
def configuracion_respaldos():
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
@admin_required
def guardar_configuracion_respaldos():
    """Guarda la configuración de respaldos automáticos"""
    
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
        configurar_scheduler()
        
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
        
        ventas, cantidad = generar_backup_completo()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archivos_generados = []
        
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
        
        from services.auto_backup_service import agregar_historial

        # Guardamos en el historial de respaldos (cantidad_registros debe ser int)
        tablas_respaldadas = {nombre: len(datos) for nombre, datos in ventas.items()} if isinstance(ventas, dict) else {}
        agregar_historial(
            tipo_respaldo="manual",
            formato=formato,
            cantidad_registros=cantidad,
            tablas_respaldadas=tablas_respaldadas,
            archivos_generados=archivos_generados,
            estado="manual"
        )
        
        flash(f"✅ Respaldo manual ejecutado: {cantidad} registros, {len(archivos_generados)} archivo(s) generado(s).", "success")
        
        return redirect("/respaldos/centro-descargas")
        
    except Exception as e:
        flash(f"❌ Error al ejecutar respaldo manual: {str(e)}", "danger")
        return redirect("/respaldos/configuracion")

@app.route("/respaldos/centro-descargas")
def centro_descargas():
    """Centro de descargas - Muestra archivos listos para descargar"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    archivos = listar_archivos_guardados()
    config = cargar_config()
    
    pendientes = sum(1 for a in archivos if a.get("es_nuevo", False))
    
    return render_template(
        "centro_descargas.html",
        archivos=archivos,
        pendientes=pendientes,
        dias_retener=config.get("dias_retener", 30)
    )

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
        filepath = os.path.join(BACKUPS_STORAGE_DIR, filename)
        
        if not os.path.exists(filepath):
            flash("Archivo no encontrado.", "danger")
            return redirect("/respaldos/archivos")
        
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
        config = cargar_config()
        dias = config.get("dias_retener", 30)
        
        from services.auto_backup_service import limpiar_backups_antiguos
        limpiar_backups_antiguos(dias)
        
        flash(f"✅ Limpieza completada. Archivos más antiguos que {dias} días eliminados.", "success")
    
    except Exception as e:
        flash(f"❌ Error al limpiar archivos: {str(e)}", "danger")
    
    return redirect("/respaldos/archivos")

@app.route("/respaldos/forzar-ejecucion", methods=["POST"])
def forzar_ejecucion_respaldo():
    """Fuerza la ejecución del respaldo automático inmediatamente"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    try:
        ejecutar_respaldo_programado()
        flash("✅ Respaldo automático ejecutado. Ve al Centro de Descargas para descargar los archivos.", "success")
        return redirect("/respaldos/centro-descargas")
    except Exception as e:
        flash(f"❌ Error al forzar ejecución: {str(e)}", "danger")
        return redirect("/respaldos/configuracion")

@app.route('/respaldos/ejecutar-prueba', methods=['POST'])
def ejecutar_prueba_respaldo():
    """Ejecuta un respaldo de prueba y (si está activo) envía el correo."""
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "No autorizado"}), 401

    try:
        from services.auto_backup_service import ejecutar_respaldo_prueba
        from services.email_service import cargar_config_email, enviar_email_respaldo

        success, message, archivos_paths, total_registros, tablas_respaldadas = ejecutar_respaldo_prueba()

        if not success:
            return jsonify({"success": False, "message": message})

        # Envío de correo si está configurado
        email_config = cargar_config_email()
        if email_config.get("activo", False):
            try:
                sent, mail_message = enviar_email_respaldo(
                    archivos_paths,
                    "prueba",
                    total_registros,
                    tablas_respaldadas
                )
                if sent:
                    message += " | Correo enviado correctamente."
                else:
                    message += f" | Error al enviar correo: {mail_message}"
            except Exception as e:
                message += f" | Error al enviar correo: {str(e)}"

        return jsonify({"success": True, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error inesperado: {str(e)}"}), 500

# ======================== API PARA CONFIGURACIÓN DE RESPALDOS ========================
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
    return jsonify(historial[:10])

@app.route('/respaldos/api/archivos-recientes', methods=['GET'])
def api_archivos_recientes():
    """API para obtener archivos recientes"""
    from services.auto_backup_service import listar_archivos_guardados
    
    archivos = listar_archivos_guardados()
    return jsonify(archivos[:5])

@app.route('/respaldos/api/config-email', methods=['GET'])
def api_config_email():
    """API para obtener la configuración de envío de correos"""
    if not session.get("logged_in"):
        return jsonify({"error": "No autorizado"}), 401

    from services.email_service import cargar_config_email
    config = cargar_config_email()
    return jsonify({
        "activo": config.get("activo", False),
        "emails_destino": config.get("emails_destino", []),
        "incluir_adjuntos": config.get("incluir_adjuntos", True)
    })

@app.route('/respaldos/api/config-email/guardar', methods=['POST'])
def api_guardar_config_email():
    """API para guardar la configuración de envío de correos"""
    if not session.get("logged_in"):
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json(silent=True) or {}
    activo = bool(data.get("activo", False))
    emails_destino = data.get("emails_destino") or []
    incluir_adjuntos = bool(data.get("incluir_adjuntos", True))

    if activo and (not isinstance(emails_destino, list) or len(emails_destino) == 0):
        return jsonify({"success": False, "message": "Debes configurar al menos un correo de destino."}), 400

    try:
        from services.email_service import cargar_config_email, guardar_config_email, validar_configuracion_email

        config = cargar_config_email()
        config.update({
            "activo": activo,
            "emails_destino": emails_destino,
            "incluir_adjuntos": incluir_adjuntos
        })
        guardar_config_email(config)

        valido, mensaje = validar_configuracion_email()
        return jsonify({"success": True, "message": mensaje})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error al guardar configuración: {str(e)}"}), 500

@app.route('/respaldos/api/email/prueba', methods=['POST'])
def api_email_prueba():
    """API para enviar un correo de prueba"""
    if not session.get("logged_in"):
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json(silent=True) or {}
    emails_destino = data.get("emails_destino") or []

    if not isinstance(emails_destino, list) or len(emails_destino) == 0:
        return jsonify({"success": False, "message": "Debes agregar al menos un correo de destino para la prueba."}), 400

    try:
        from services.email_service import cargar_config_email, guardar_config_email, enviar_correo_prueba

        config = cargar_config_email()
        config["activo"] = True
        config["emails_destino"] = emails_destino
        guardar_config_email(config)

        success, message = enviar_correo_prueba()
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error al enviar correo: {str(e)}"}), 500

# ======================== RECUPERACIÓN DE CONTRASEÑA ========================
@app.route("/recuperar-password", methods=["POST"])
def recuperar_password():
    """Solicita un código de recuperación"""
    from services.auth_service import crear_codigo_recuperacion
    from services.email_service import enviar_codigo_recuperacion
    
    # Aceptamos tanto 'correo' como 'email' desde el formulario
    correo = request.form.get("correo", "").strip() or request.form.get("email", "").strip()
    
    if not correo:
        flash("Por favor ingresa tu correo electrónico.", "danger")
        return redirect("/login")
    
    success, codigo, mensaje = crear_codigo_recuperacion(correo)
    
    if not success:
        flash(mensaje, "danger")
        return redirect("/login")
    
    enviado, msg_correo = enviar_codigo_recuperacion(correo, codigo)
    
    if enviado:
        session['recovery_correo'] = correo
        session['recovery_step'] = 2
        
        flash(f"✅ Código enviado a tu correo. Revisa tu bandeja de entrada.", "success")
        return redirect("/login#recovery")
    else:
        flash(f"❌ Error al enviar el correo: {msg_correo}", "danger")
        return redirect("/login")

@app.route("/restablecer-password", methods=["POST"])
def restablecer_password_route():
    """Restablece la contraseña con el código"""
    from services.auth_service import restablecer_password
    
    correo = session.get('recovery_correo')
    
    if not correo:
        flash("⚠️ Sesión expirada. Solicita un nuevo código.", "warning")
        return redirect("/login")
    
    codigo = request.form.get("codigo", "").strip()
    nueva_password = request.form.get("nueva_password", "")
    confirmar_password = request.form.get("confirmar_password", "")
    
    if not all([codigo, nueva_password, confirmar_password]):
        flash("Todos los campos son obligatorios.", "danger")
        return redirect("/login#recovery")
    
    if nueva_password != confirmar_password:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect("/login#recovery")
    
    if len(nueva_password) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "danger")
        return redirect("/login#recovery")
    
    success, mensaje = restablecer_password(correo, codigo, nueva_password)
    
    if success:
        session.pop('recovery_correo', None)
        session.pop('recovery_step', None)
        
        flash("✅ Contraseña restablecida exitosamente. Ahora puedes iniciar sesión.", "success")
        return redirect("/login")
    else:
        flash(f"❌ {mensaje}", "danger")
        return redirect("/login#recovery")

@app.route("/cancelar-recuperacion")
def cancelar_recuperacion():
    """Cancela el proceso de recuperación y limpia la sesión"""
    session.pop('recovery_correo', None)
    session.pop('recovery_step', None)
    flash("Proceso de recuperación cancelado.", "info")
    return redirect("/login")

# ======================== RESTAURACIÓN DE RESPALDOS ========================
from services.restore_service import (
    cargar_historial_restauraciones, 
    obtener_estadisticas_restauraciones,
    validar_archivo_restauracion,
    restaurar_desde_sql,
    restaurar_desde_excel,
    restaurar_desde_json,
    guardar_historial_restauraciones,
    agregar_historial_restauracion
)

@app.route("/restaurar")
def restaurar_respaldos():
    """Página de restauración de respaldos"""
    if not session.get("logged_in"):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect("/login")
    
    if session.get("user_role") != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect("/dashboard")
    
    historial = cargar_historial_restauraciones()[:10]
    estadisticas = obtener_estadisticas_restauraciones()
    
    for item in historial:
        try:
            fecha_dt = datetime.fromisoformat(item["fecha"])
            item["fecha"] = fecha_dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    return render_template(
        "restaurar.html",
        historial=historial,
        estadisticas=estadisticas
    )

@app.route("/restaurar/subir", methods=["POST"])
def subir_archivo_restauracion():
    """Procesa el archivo de restauración subido"""
    if not session.get("logged_in"):
        return redirect("/login")
    
    if session.get("user_role") != "admin":
        flash("No tienes permisos para realizar esta acción.", "danger")
        return redirect("/dashboard")
    
    if 'archivo' not in request.files:
        flash("❌ No se seleccionó ningún archivo.", "danger")
        return redirect("/restaurar")
    
    file = request.files['archivo']
    
    if file.filename == '':
        flash("❌ No se seleccionó ningún archivo.", "danger")
        return redirect("/restaurar")
    
    valido, extension, mensaje = validar_archivo_restauracion(file.filename)
    
    if not valido:
        flash(f"❌ {mensaje}", "danger")
        return redirect("/restaurar")
    
    try:
        file_content = file.read()
        
        if extension == '.sql':
            success, mensaje, stats = restaurar_desde_sql(file_content)
        elif extension == '.xlsx':
            success, mensaje, stats = restaurar_desde_excel(file_content)
        elif extension == '.json':
            success, mensaje, stats = restaurar_desde_json(file_content)
        else:
            flash("❌ Formato de archivo no soportado.", "danger")
            return redirect("/restaurar")
        
        if success:
            tablas = stats.get("tablas", [])
            total_registros = stats.get("total_registros", 0)
            agregar_historial_restauracion(extension[1:], tablas, total_registros, "exitoso")

            flash(f"✅ {mensaje}", "success")
            if tablas:
                flash(f"📂 Tablas restauradas: {', '.join(tablas)}", "info")
            flash(f"📊 Registros restaurados: {total_registros}", "info")

            if stats.get("detalles"):
                detalles = "<br>".join([f"📂 {col}: {cant} registros" for col, cant in stats["detalles"].items()])
                flash(f"Detalles de la restauración:<br>{detalles}", "info")
        else:
            agregar_historial_restauracion(extension[1:], [], 0, "fallido", str(mensaje))
            flash(f"❌ {mensaje}", "danger")
    
    except Exception as e:
        flash(f"❌ Error al procesar archivo: {str(e)}", "danger")
        import traceback
        traceback.print_exc()
    
    return redirect("/restaurar")

@app.route("/restaurar/historial")
def historial_restauraciones():
    """Retorna el historial completo de restauraciones en JSON"""
    if not session.get("logged_in"):
        return {"error": "No autorizado"}, 401
    
    historial = cargar_historial_restauraciones()
    return jsonify(historial)

@app.route("/restaurar/limpiar-historial", methods=["POST"])
def limpiar_historial_restauraciones():
    """Limpia completamente el historial de restauraciones"""
    if not session.get("logged_in"):
        return jsonify({"success": False, "message": "No autorizado"}), 401
    
    if session.get("user_role") != "admin":
        return jsonify({"success": False, "message": "No tienes permisos"}), 403
    
    try:
        guardar_historial_restauraciones([])
        return jsonify({
            "success": True,
            "message": "Historial limpiado exitosamente"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al limpiar historial: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)