"""
Serviço de envio de mensagens WhatsApp via WAHA (local Docker).
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_report_whatsapp(phone: str, message: str) -> dict:
    """
    Envia o relatório via WhatsApp usando a instância WAHA local.
    O número deve estar no formato internacional (ex: +34612345678).
    Retorna dict com success=True em caso de êxito, ou lança exceção.
    """
    # Normaliza número: remove +, espaços e hífens
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    chat_id = f"{clean_phone}@c.us"

    try:
        response = requests.post(
            f"{settings.WAHA_URL}/api/sendText",
            json={
                "chatId": chat_id,
                "text": message,
                "session": settings.WAHA_SESSION,
            },
            timeout=15,
        )
        response.raise_for_status()
        logger.info("WhatsApp enviado para %s", phone)
        return {"success": True}
    except requests.RequestException as e:
        logger.error(
            "Erro ao enviar WhatsApp para %s: %s",
            phone,
            e,
            exc_info=True,
        )
        raise
