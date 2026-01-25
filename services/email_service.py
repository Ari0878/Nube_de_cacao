# services/email_service.py

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Directorio para configuración de email
EMAIL_CONFIG_DIR = "email_config"
if not os.path.exists(EMAIL_CONFIG_DIR):
    os.makedirs(EMAIL_CONFIG_DIR)

CONFIG_FILE = os.path.join(EMAIL_CONFIG_DIR, "email_config.json")


def cargar_config_email():
    """Carga la configuración de email"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Configuración por defecto - CREDENCIALES FIJAS (ocultas al usuario)
    return {
        "activo": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_from": "al222310566@gmail.com",  # FIJO - No se muestra al usuario
        "email_password": "bzjtagkbebehqfkb",  # FIJO - No se muestra al usuario
        "emails_destino": [],  # ÚNICO campo que el usuario configura
        "incluir_adjuntos": True,
        "max_size_mb": 25
    }


def guardar_config_email(config):
    """Guarda la configuración de email"""
    # Asegurar que las credenciales fijas siempre estén presentes
    config["email_from"] = "al222310566@gmail.com"
    config["email_password"] = "bzjt agkb ebeh qfkb"
    config["smtp_server"] = "smtp.gmail.com"
    config["smtp_port"] = 587
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def validar_configuracion_email():
    """Valida que la configuración de email esté completa"""
    config = cargar_config_email()
    
    if not config.get("activo"):
        return False, "El envío de correos está desactivado"
    
    if not config.get("emails_destino") or len(config.get("emails_destino", [])) == 0:
        return False, "No se han configurado correos de destino"
    
    return True, "Configuración válida"


def enviar_email_respaldo(archivos_paths, tipo_respaldo, cantidad_registros, colecciones_info):
    """
    Envía un correo con los archivos de respaldo adjuntos
    
    Args:
        archivos_paths: Lista de rutas completas a los archivos
        tipo_respaldo: Tipo de respaldo (completo, incremental, diferencial)
        cantidad_registros: Número total de registros respaldados
        colecciones_info: Diccionario con información de colecciones
    
    Returns:
        (success: bool, message: str)
    """
    # Validar configuración
    valido, mensaje = validar_configuracion_email()
    if not valido:
        return False, mensaje
    
    config = cargar_config_email()
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = config["email_from"]
        msg['To'] = ", ".join(config["emails_destino"])
        msg['Subject'] = f"🔒 Respaldo Automático - Nube de Cacao ({tipo_respaldo.upper()})"
        
        # Cuerpo del correo
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
                tamaño = os.path.getsize(filepath) / (1024 * 1024)  # MB
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
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #4A2C2A, #8B4513);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    border-left: 4px solid #DAA520;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th {{
                    background: #4A2C2A;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                .footer {{
                    background: #333;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 0 0 10px 10px;
                    font-size: 12px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    background: #28a745;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                }}
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
                        <tr>
                            <th>Colección</th>
                            <th style="text-align: center;">Registros</th>
                        </tr>
                        {colecciones_html}
                    </table>
                    
                    <h3>📁 Archivos Adjuntos</h3>
                    <table>
                        <tr>
                            <th>Archivo</th>
                            <th style="text-align: center;">Tamaño</th>
                        </tr>
                        {archivos_html}
                    </table>
                    
                    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-top: 20px; border-radius: 5px;">
                        <p style="margin: 0;"><strong>⚠️ Importante:</strong></p>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>Guarda estos archivos en un lugar seguro</li>
                            <li>Verifica que los archivos se hayan descargado correctamente</li>
                            <li>Los archivos contienen información sensible de tu negocio</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">Nube de Cacao - Sistema de Respaldos Automáticos</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Este correo fue generado automáticamente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Adjuntar archivos si está configurado
        if config.get("incluir_adjuntos", True):
            max_size_bytes = config.get("max_size_mb", 25) * 1024 * 1024
            
            # Verificar tamaño total
            if tamaño_total * 1024 * 1024 > max_size_bytes:
                return False, f"Los archivos superan el límite de {config.get('max_size_mb', 25)} MB"
            
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
        
        # Conectar y enviar
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["email_from"], config["email_password"])
        
        text = msg.as_string()
        server.sendmail(config["email_from"], config["emails_destino"], text)
        server.quit()
        
        return True, f"Correo enviado exitosamente a {len(config['emails_destino'])} destinatario(s)"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación. Verifica la configuración del servidor"
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {str(e)}"
    except Exception as e:
        return False, f"Error al enviar correo: {str(e)}"


def enviar_correo_prueba():
    """
    Envía un correo de prueba para verificar la configuración
    """
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
                    <p>Este es un correo de prueba para verificar que la configuración de envío de correos funciona correctamente.</p>
                    <p><strong>Si recibes este correo, significa que:</strong></p>
                    <ul>
                        <li>✅ El servidor SMTP está configurado correctamente</li>
                        <li>✅ Las credenciales son válidas</li>
                        <li>✅ Los correos de destino están bien configurados</li>
                    </ul>
                    <p>Ahora puedes recibir respaldos automáticos por correo electrónico.</p>
                </div>
                <div class="footer">
                    <p style="margin: 0;">Nube de Cacao - Sistema de Respaldos</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        print(f"Intentando conectar a {config['smtp_server']}:{config['smtp_port']}")
        print(f"Usuario: {config['email_from']}")
        print(f"Destinatarios: {config['emails_destino']}")
        
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=30)
        server.set_debuglevel(1)  # Activar debug para ver más detalles
        server.starttls()
        
        print("Intentando login...")
        server.login(config["email_from"], config["email_password"])
        print("Login exitoso")
        
        text = msg.as_string()
        server.sendmail(config["email_from"], config["emails_destino"], text)
        server.quit()
        
        print("Correo enviado exitosamente")
        return True, "Correo de prueba enviado exitosamente"
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Error de autenticación SMTP: {str(e)}"
        print(error_msg)
        return False, "Error de autenticación. Verifica que la contraseña de aplicación sea correcta"
    
    except smtplib.SMTPConnectError as e:
        error_msg = f"Error de conexión SMTP: {str(e)}"
        print(error_msg)
        return False, "No se pudo conectar al servidor de correo"
    
    except smtplib.SMTPException as e:
        error_msg = f"Error SMTP: {str(e)}"
        print(error_msg)
        return False, f"Error SMTP: {str(e)}"
    
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False, f"Error al enviar correo: {str(e)}"

