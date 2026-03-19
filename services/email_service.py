# services/email_service.py

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

EMAIL_CONFIG_DIR = "email_config"
if not os.path.exists(EMAIL_CONFIG_DIR):
    os.makedirs(EMAIL_CONFIG_DIR)

CONFIG_FILE = os.path.join(EMAIL_CONFIG_DIR, "email_config.json")


def cargar_config_email():
    """Carga la configuración de email"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        "activo": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_from": "al222310566@gmail.com",
        "email_password": "bzjtagkbebehqfkb",
        "emails_destino": [],
        "incluir_adjuntos": True,
        "max_size_mb": 25
    }


def guardar_config_email(config):
    """Guarda la configuración de email"""
    # Tomamos la configuración existente y la actualizamos con los valores nuevos
    base = cargar_config_email()
    base.update(config or {})

    # Si la contraseña fue copiada/pegada con espacios (error común), los removemos
    if base.get("email_password"):
        base["email_password"] = base["email_password"].replace(" ", "")

    # Valores por defecto seguros/esperados
    base.setdefault("smtp_server", "smtp.gmail.com")
    base.setdefault("smtp_port", 587)
    base.setdefault("email_from", "al222310566@gmail.com")
    base.setdefault("email_password", "bzjtagkbebehqfkb")
    base.setdefault("emails_destino", [])
    base.setdefault("incluir_adjuntos", True)
    base.setdefault("max_size_mb", 25)

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=2)


def validar_configuracion_email():
    """Valida que la configuración de email esté completa"""
    config = cargar_config_email()
    
    if not config.get("activo"):
        return False, "El envío de correos está desactivado"
    
    if not config.get("emails_destino") or len(config.get("emails_destino", [])) == 0:
        return False, "No se han configurado correos de destino"
    
    return True, "Configuración válida"


def enviar_email_respaldo(archivos_paths, tipo_respaldo, cantidad_registros, colecciones_info):
    """Envía un correo con los archivos de respaldo adjuntos"""
    valido, mensaje = validar_configuracion_email()
    if not valido:
        return False, mensaje
    
    config = cargar_config_email()
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config["email_from"]
        msg['To'] = ", ".join(config["emails_destino"])
        msg['Subject'] = f"🔒 Respaldo Automático - Nube de Cacao ({tipo_respaldo.upper()})"
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        colecciones_html = ""
        for nombre, cantidad in colecciones_info.items():
            colecciones_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{nombre}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{cantidad}</td>
            </tr>
            """
        
        archivos_html = ""
        tamaño_total = 0
        for filepath in archivos_paths:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                tamaño = os.path.getsize(filepath) / (1024 * 1024)
                tamaño_total += tamaño
                archivos_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">📎 {filename}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{tamaño:.2f} MB</td>
                </tr>
                """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4A2C2A, #8B4513); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                .info-box {{ background: white; border-left: 4px solid #DAA520; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background: #4A2C2A; color: white; padding: 12px; text-align: left; }}
                .footer {{ background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; }}
                .badge {{ display: inline-block; padding: 5px 15px; background: #28a745; color: white; border-radius: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>☕ Nube de Cacao</h1>
                    <h2>Respaldo Automático Completado</h2>
                    <p style="margin: 0;">Sistema de Gestión de Ventas</p>
                </div>
                <div class="content">
                    <div class="info-box">
                        <h3 style="margin-top: 0;">✅ Respaldo Ejecutado Exitosamente</h3>
                        <p><strong>Fecha:</strong> {fecha_actual}</p>
                        <p><strong>Tipo:</strong> <span class="badge">{tipo_respaldo.upper()}</span></p>
                        <p><strong>Total de Registros:</strong> {cantidad_registros}</p>
                        <p><strong>Archivos Adjuntos:</strong> {len(archivos_paths)}</p>
                        <p><strong>Tamaño Total:</strong> {tamaño_total:.2f} MB</p>
                    </div>
                    <h3>📊 Colecciones Respaldadas</h3>
                    <table>
                        <tr><th>Colección</th><th style="text-align: center;">Registros</th></tr>
                        {colecciones_html}
                    </table>
                    <h3>📁 Archivos Adjuntos</h3>
                    <table>
                        <tr><th>Archivo</th><th style="text-align: center;">Tamaño</th></tr>
                        {archivos_html}
                    </table>
                </div>
                <div class="footer">
                    <p style="margin: 0;">Nube de Cacao - Sistema de Respaldos Automáticos</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        if config.get("incluir_adjuntos", True):
            for filepath in archivos_paths:
                if not os.path.exists(filepath):
                    continue
                
                filename = os.path.basename(filepath)
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(part)
        
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["email_from"], config["email_password"])
        
        text = msg.as_string()
        server.sendmail(config["email_from"], config["emails_destino"], text)
        server.quit()
        
        return True, f"Correo enviado exitosamente a {len(config['emails_destino'])} destinatario(s)"
    
    except Exception as e:
        return False, f"Error al enviar correo: {str(e)}"


def enviar_codigo_recuperacion(correo_destino, codigo):
    """
    Envía un código de recuperación de contraseña por correo
    Args:
        correo_destino: Email del usuario
        codigo: Código de 6 dígitos
    Returns:
        (success: bool, mensaje: str)
    """
    config = cargar_config_email()
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config["email_from"]
        msg['To'] = correo_destino
        msg['Subject'] = "🔐 Código de Recuperación - Nube de Cacao"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #4A2C2A, #8B4513); color: white; padding: 40px 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 40px 30px; border-left: 1px solid #ddd; border-right: 1px solid #ddd; }}
                .code-box {{ background: white; border: 3px dashed #DAA520; padding: 30px; margin: 30px 0; text-align: center; border-radius: 10px; }}
                .code {{ font-size: 48px; font-weight: bold; color: #4A2C2A; letter-spacing: 10px; font-family: 'Courier New', monospace; }}
                .footer {{ background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .btn {{ display: inline-block; padding: 12px 30px; background: #DAA520; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 32px;">☕ Nube de Cacao</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Recuperación de Contraseña</p>
                </div>
                
                <div class="content">
                    <h2 style="color: #4A2C2A; margin-top: 0;">Código de Verificación</h2>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña. Usa el siguiente código para continuar:</p>
                    
                    <div class="code-box">
                        <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Tu código de verificación es:</p>
                        <div class="code">{codigo}</div>
                        <p style="margin: 15px 0 0 0; color: #666; font-size: 12px;">Este código expira en <strong>15 minutos</strong></p>
                    </div>
                    
                    <div class="warning">
                        <p style="margin: 0;"><strong>⚠️ Importante:</strong></p>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>No compartas este código con nadie</li>
                            <li>Si no solicitaste este cambio, ignora este correo</li>
                            <li>El código solo funciona una vez</li>
                            <li>Tienes 3 intentos para ingresar el código correcto</li>
                        </ul>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        Si tienes problemas, contacta con soporte o solicita un nuevo código.
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">Nube de Cacao - Sistema de Gestión</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Este correo fue generado automáticamente</p>
                    <p style="margin: 10px 0 0 0; opacity: 0.6; font-size: 11px;">© {datetime.now().year} Nube de Cacao. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
        server.starttls()
        server.login(config["email_from"], config["email_password"])
        
        server.sendmail(config["email_from"], correo_destino, msg.as_string())
        server.quit()
        
        return True, "Código enviado exitosamente"
    
    except Exception as e:
        print(f"Error al enviar código: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error al enviar código: {str(e)}"


def enviar_correo_prueba():
    """Envía un correo de prueba para verificar la configuración"""
    config = cargar_config_email()
    
    valido, mensaje = validar_configuracion_email()
    if not valido:
        return False, mensaje
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config["email_from"]
        msg['To'] = ", ".join(config["emails_destino"])
        msg['Subject'] = "✅ Prueba de Configuración - Nube de Cacao"
        
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }
                .footer { background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Prueba Exitosa</h1>
                    <h2>Nube de Cacao</h2>
                </div>
                <div class="content">
                    <h3>Configuración de Correo Verificada</h3>
                    <p>La configuración funciona correctamente.</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">Nube de Cacao - Sistema de Respaldos</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
        server.starttls()
        server.login(config["email_from"], config["email_password"])
        
        server.sendmail(config["email_from"], config["emails_destino"], msg.as_string())
        server.quit()
        
        return True, "Correo de prueba enviado exitosamente"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error al enviar correo: {str(e)}"