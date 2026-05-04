---
description: Padrões para integração com APIs externas no ReportAI.
---

# Skill: API Integration Patterns — ReportAI

## Configuração de Conexão com Supabase (Produção)
```python
# DATABASE_URL em produção deve usar porta 6543 (PgBouncer Transaction mode)
# Exemplo: postgres://user:pass@host:6543/dbname
# Em dev: SQLite local via default do dj_database_url
```

## Google Ads API — Buscar Campanhas
```python
from google.ads.googleads.client import GoogleAdsClient

def get_google_ads_campaigns(customer_id: str, credentials: dict) -> list[dict]:
    """Busca campanhas ativas de uma conta Google Ads."""
    client = GoogleAdsClient.load_from_dict(credentials)
    service = client.get_service("GoogleAdsService")
    query = '''
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    '''
    response = service.search(customer_id=customer_id, query=query)
    return [
        {"id": str(row.campaign.id), "name": row.campaign.name}
        for row in response
    ]
```

## Meta Ads API — Buscar Campanhas
```python
import requests

def get_meta_campaigns(ad_account_id: str, access_token: str) -> list[dict]:
    """Busca campanhas ativas de uma conta Meta Ads."""
    url = f"https://graph.facebook.com/v19.0/{ad_account_id}/campaigns"
    params = {
        "fields": "id,name,status,effective_status",
        "effective_status": '["ACTIVE","PAUSED"]',
        "access_token": access_token,
        "limit": 100
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("data", [])
```

## Evolution API — Enviar Mensagem WhatsApp
```python
import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone: str, message: str) -> dict:
    """Envia mensagem de texto via Evolution API (WhatsApp)."""
    api_url = os.environ.get('EVOLUTION_API_URL')
    api_key = os.environ.get('EVOLUTION_API_KEY')
    instance = os.environ.get('EVOLUTION_INSTANCE')

    response = requests.post(
        f"{api_url}/message/sendText/{instance}",
        headers={
            "apikey": api_key,
            "Content-Type": "application/json"
        },
        json={
            "number": phone,
            "text": message
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

## Resend — Enviar E-mail
```python
import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, html_content: str) -> dict:
    """Envia e-mail via Resend API."""
    api_key = os.environ.get('RESEND_API_KEY')
    from_email = os.environ.get('RESEND_FROM_EMAIL', 'reports@getreportai.com')

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": html_content
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

## Grok API — Gerar Texto Humanizado
```python
import os
import requests
import logging

logger = logging.getLogger(__name__)

def generate_humanized_text(prompt: str) -> str:
    """Gera texto humanizado usando Grok API."""
    api_key = os.environ.get('GROK_API_KEY')

    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-3",
            "messages": [
                {"role": "system", "content": "Eres un analista de marketing digital experto."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
```

## Padrão de Tratamento de Erros (OBRIGATÓRIO)
```python
import logging
from time import sleep

logger = logging.getLogger(__name__)

def api_call_with_retry(func, max_retries=3, base_delay=2):
    """Wrapper genérico com retry e backoff exponencial."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            last_exception = e
            if e.response.status_code == 429:
                delay = base_delay ** (attempt + 1)
                logger.warning("Rate limit, aguardando %ds (tentativa %d/%d)", delay, attempt + 1, max_retries)
                sleep(delay)
            elif e.response.status_code in (401, 403):
                logger.error("Erro de autenticação: %s", e)
                raise  # não retry para auth errors
            else:
                logger.error("HTTP error: %s", e)
                raise
        except requests.exceptions.Timeout:
            last_exception = e
            logger.warning("Timeout (tentativa %d/%d)", attempt + 1, max_retries)
            sleep(base_delay)
        except Exception as e:
            logger.error("Erro inesperado: %s", e)
            raise
    raise last_exception or Exception("Máximo de tentativas excedido")
```
