"""Servicio de envío de correos electrónicos vía SMTP para FashionStore.

Utiliza smtplib nativo de Python ejecutado de forma asíncrona mediante
asyncio.to_thread para evitar bloqueos del bucle de eventos de FastAPI (CU33).
Incorpora cabeceras RFC 5322, RFC 3834 y optimización de contenido para
máxima entregabilidad en bandeja de entrada principal (evitando carpetas de Spam).
"""

import asyncio
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import logging
import smtplib
from typing import Optional

from core.config import settings

logger = logging.getLogger("fashionstore.email")


def _generar_cuerpo_html(codigo: str, destinatario: str) -> str:
    """Genera la plantilla HTML transaccional limpia con estética editorial Haute Couture.
    
    Diseñada siguiendo las directrices de entregabilidad de Google y Microsoft:
    - Sin palabras de riesgo de phishing (elimina reclamos criptográficos agresivos).
    - Sin emojis en el cuerpo ni en las tablas que disparen filtros bayesianos.
    - Ratio texto/HTML equilibrado y maquetación compatible con clientes modernos.
    """
    codigo_formateado = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Código de verificación de Fashion Store</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8F7F4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #18181B;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #F8F7F4; padding: 40px 16px;">
    <tr>
      <td align="center">
        <!-- Tarjeta Principal -->
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 480px; background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E4E4E7; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04); overflow: hidden; padding: 36px 28px;">
          
          <!-- Monograma Superior FS -->
          <tr>
            <td align="center" style="padding-bottom: 20px;">
              <table border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center" style="width: 44px; height: 44px; background-color: #18181B; border-radius: 12px; color: #FFFFFF; font-size: 16px; font-weight: 700; letter-spacing: 1px;">
                    FS
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Identidad de Marca -->
          <tr>
            <td align="center" style="padding-bottom: 6px;">
              <p style="margin: 0; font-size: 11px; font-weight: 600; letter-spacing: 2px; color: #71717A; text-transform: uppercase;">
                Recuperación de Acceso
              </p>
              <h1 style="margin: 6px 0 0 0; font-size: 22px; font-weight: 800; letter-spacing: 1.5px; color: #18181B; text-transform: uppercase;">
                Fashion Store
              </h1>
            </td>
          </tr>

          <!-- Mensaje Explicativo -->
          <tr>
            <td align="center" style="padding: 16px 8px 24px 8px;">
              <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #52525B;">
                Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Utiliza el siguiente código de verificación temporal:
              </p>
            </td>
          </tr>

          <!-- Caja de Código OTP Destacado -->
          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <div style="background-color: #F4F4F5; border: 1px solid #E4E4E7; border-radius: 12px; padding: 18px 28px; display: inline-block;">
                <p style="margin: 0 0 4px 0; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: #71717A; text-transform: uppercase;">
                  Código de verificación
                </p>
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #09090B; display: block;">
                  {codigo_formateado}
                </span>
              </div>
            </td>
          </tr>

          <!-- Información de Validez y Seguridad -->
          <tr>
            <td style="padding-bottom: 20px; border-top: 1px solid #F4F4F5; padding-top: 18px;">
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #71717A; text-align: center;">
                Este código es de uso único y caduca en <strong>{settings.OTP_EXPIRE_MINUTES} minutos</strong>.
              </p>
              <p style="margin: 8px 0 0 0; font-size: 12px; line-height: 1.5; color: #A1A1AA; text-align: center;">
                Si tú no has solicitado este restablecimiento, puedes desestimar este mensaje de forma segura. Tu cuenta no ha sufrido ninguna modificación.
              </p>
            </td>
          </tr>

          <!-- Pie de Tarjeta Institucional -->
          <tr>
            <td align="center" style="border-top: 1px solid #F4F4F5; padding-top: 16px;">
              <p style="margin: 0; font-size: 11px; font-weight: 500; color: #A1A1AA;">
                Fashion Store Atelier · Notificación automática del sistema
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _generar_cuerpo_texto_plano(codigo: str) -> str:
    """Genera la versión en texto plano para clientes sin soporte HTML."""
    codigo_formateado = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo
    return f"""FASHION STORE — RECUPERACIÓN DE ACCESO

Hola,

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
Tu código de verificación de 6 dígitos es:

CÓDIGO: {codigo_formateado}

- Este código es de uso único y expira en {settings.OTP_EXPIRE_MINUTES} minutos.
- Si tú no solicitaste este cambio, puedes ignorar este correo de forma segura. Tu contraseña actual no ha sido modificada.

Atentamente,
Fashion Store Atelier
"""


def _enviar_smtp_sync(destinatario: str, codigo: str) -> bool:
    """Envío sincrónico del correo mediante smtplib con STARTTLS y cabeceras anti-spam RFC."""
    codigo_formateado = f"{codigo[:3]} {codigo[3:]}" if len(codigo) == 6 else codigo

    mensaje = MIMEMultipart("alternative")
    
    # Asunto optimizado para entregabilidad transaccional sin palabras gatillo de spam
    asunto_texto = f"Tu código de recuperación Fashion Store: {codigo_formateado}"
    mensaje["Subject"] = Header(asunto_texto, "utf-8")
    
    # Cabeceras RFC requeridas para autenticidad y reputación de entrega
    mensaje["From"] = email.utils.formataddr((settings.SMTP_FROM_NAME, settings.SMTP_USER))
    mensaje["To"] = destinatario
    mensaje["Reply-To"] = settings.SMTP_USER
    mensaje["Date"] = email.utils.formatdate(localtime=True)
    
    # Extracción de dominio para Message-ID RFC 5322
    dominio = settings.SMTP_USER.split("@")[-1] if "@" in settings.SMTP_USER else "fashionstore.com"
    mensaje["Message-ID"] = email.utils.make_msgid(domain=dominio)
    
    # Declaración de correo transaccional automático (RFC 3834)
    mensaje["Auto-Submitted"] = "auto-generated"
    mensaje["X-Auto-Response-Suppress"] = "All"
    mensaje["Precedence"] = "bulk"

    # Adjuntar versiones de texto plano y HTML
    texto_plano = _generar_cuerpo_texto_plano(codigo)
    html_plano = _generar_cuerpo_html(codigo, destinatario)

    mensaje.attach(MIMEText(texto_plano, "plain", "utf-8"))
    mensaje.attach(MIMEText(html_plano, "html", "utf-8"))

    try:
        logger.info(
            "Iniciando conexion SMTP con %s:%s para destinatario %s",
            settings.SMTP_SERVER,
            settings.SMTP_PORT,
            destinatario,
        )
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=15) as servidor:
            servidor.ehlo()
            if settings.SMTP_USE_TLS:
                servidor.starttls()
                servidor.ehlo()
            servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            servidor.sendmail(settings.SMTP_USER, [destinatario], mensaje.as_string())
        logger.info("Correo de recuperacion enviado exitosamente a %s", destinatario)
        return True
    except Exception as exc:
        logger.error(
            "Fallo al enviar correo SMTP a %s: %s",
            destinatario,
            str(exc),
            exc_info=True,
        )
        raise exc


class EmailService:
    """Servicio asíncrono de notificaciones por correo electrónico."""

    async def enviar_codigo_recuperacion(self, destinatario: str, codigo: str) -> bool:
        """Despacha el correo de recuperación en un hilo en segundo plano."""
        return await asyncio.to_thread(_enviar_smtp_sync, destinatario, codigo)


email_service = EmailService()
