"""
Serviço de envio de e-mail via SendGrid.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def send_report_email(to_email: str, client_name: str, message: str) -> dict:
    """
    Envia o relatório por e-mail via SendGrid.
    Retorna dict com success=True em caso de êxito, ou lança exceção.
    """
    # Converte quebras de linha em <br> para versão HTML
    html_body = message.replace("\n", "<br>")

    payload = {
        "personalizations": [
            {"to": [{"email": to_email, "name": client_name}]}
        ],
        "from": {
            "email": settings.SENDGRID_FROM_EMAIL,
            "name": settings.SENDGRID_FROM_NAME,
        },
        "subject": f"📊 Tu resumen semanal de campañas - {client_name}",
        "content": [
            {"type": "text/plain", "value": message},
            {
                "type": "text/html",
                "value": (
                    "<div style='font-family: Arial, sans-serif; max-width: 600px; "
                    "margin: 0 auto; padding: 24px; color: #1a1a1a;'>"
                    f"<p style='line-height: 1.7; font-size: 15px;'>{html_body}</p>"
                    "<hr style='margin-top: 32px; border: none; border-top: 1px solid #e5e5e5;'>"
                    "<p style='color: #888; font-size: 12px; margin-top: 12px;'>ReportAI — reportes automáticos con IA</p>"
                    "</div>"
                ),
            },
        ],
    }

    try:
        response = requests.post(
            SENDGRID_API_URL,
            headers={
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        logger.info("Email enviado para %s (cliente: %s)", to_email, client_name)
        return {"success": True, "status_code": response.status_code}
    except requests.RequestException as e:
        logger.error(
            "Erro ao enviar email para %s: %s",
            to_email,
            e,
            exc_info=True,
        )
        raise
