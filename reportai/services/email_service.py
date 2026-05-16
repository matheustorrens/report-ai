"""
Serviço de envio de e-mail via SendGrid.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def send_report_email(
    to_email: str,
    client_name: str,
    message: str,
    agency_name: str = "",
    agency_email: str = "",
) -> dict:
    """
    Envia o relatório por e-mail via SendGrid.

    - from.email: domínio autenticado do ReportAI (settings.SENDGRID_FROM_EMAIL)
    - from.name: nome da agência (visível como remetente amigável)
    - reply_to: email da agência (respostas vão para a agência, não para o ReportAI)

    Retorna dict com success=True em caso de êxito, ou lança exceção.
    """
    # Fallback para o nome padrão do settings se a agência não informar nome
    sender_name = agency_name or settings.SENDGRID_FROM_NAME

    # Converte quebras de linha em <br> para versão HTML
    html_body = message.replace("\n", "<br>")

    payload = {
        "personalizations": [
            {"to": [{"email": to_email, "name": client_name}]}
        ],
        "from": {
            # Remetente técnico: sempre o domínio autenticado do ReportAI
            "email": settings.SENDGRID_FROM_EMAIL,
            # Nome amigável: agência (o cliente vê "Agencia Sol Marketing" no campo De:)
            "name": sender_name,
        },
        "subject": f"📊 Tu reporte semanal de campañas | {sender_name}",
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

    # Reply-to: respostas do cliente final vão para a agência, não para o ReportAI
    if agency_email:
        payload["reply_to"] = {"email": agency_email, "name": sender_name}

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
        logger.info(
            "Email enviado para %s (cliente: %s, agência: %s)",
            to_email,
            client_name,
            sender_name,
        )
        return {"success": True, "status_code": response.status_code}
    except requests.RequestException as e:
        logger.error(
            "Erro ao enviar email para %s (agência: %s): %s",
            to_email,
            sender_name,
            e,
            exc_info=True,
        )
        raise
