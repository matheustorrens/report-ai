"""
Serviço de geração de mensagens via Groq API.
Utiliza o modelo Llama 3.3 70B para gerar resumos humanizados em espanhol.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Dados mockados para testes antes de conectar as APIs reais
MOCK_METRICS = {
    "current_week": {
        "google_ads": {
            "clicks": 847,
            "impressions": 12400,
            "conversions": 34,
            "cpc": 0.43,
            "spend": 364.21,
        },
        "ga4": {
            "sessions": 2103,
            "users": 1876,
            "bounce_rate": 42.3,
            "avg_session_duration": 185,
        },
    },
    "previous_week": {
        "google_ads": {
            "clicks": 756,
            "impressions": 11200,
            "conversions": 30,
            "cpc": 0.47,
            "spend": 355.32,
        },
        "ga4": {
            "sessions": 1784,
            "users": 1621,
            "bounce_rate": 45.1,
            "avg_session_duration": 171,
        },
    },
}


def _build_prompt(client, metrics: dict) -> str:
    """Monta o prompt enviado ao Groq com contexto do cliente e métricas."""
    if client.knowledge_level == 'leigo':
        knowledge_instruction = (
            "Usa lenguaje de negocio (leads, clientes, inversión). "
            "Evita términos técnicos como CPC, CTR, ROAS, sesiones."
        )
    else:
        knowledge_instruction = (
            "Puedes usar términos técnicos (ROAS, CPC, CTR, sesiones, tasa de rebote) "
            "y citar métricas por plataforma cuando sea relevante."
        )

    current = json.dumps(metrics.get("current_week", {}), ensure_ascii=False)
    previous = json.dumps(metrics.get("previous_week", {}), ensure_ascii=False)

    return f"""Eres un analista de marketing que escribe resúmenes semanales para clientes de agencias.
Escribe UN solo mensaje corto (máximo 5 líneas) en español, tono humano y directo.

Reglas del mensaje:
- NUNCA cites plataformas separadamente (no escribas "en Google Ads..." y "en GA4..." por separado)
- Sintetiza los datos en un resultado de negocio (leads, coste, tráfico)
- Destaca solo el insight más relevante de la semana (mayor variación positiva o negativa)
- Termina con una línea de estado: 🟢 Todo en orden / 🟡 Hay algo a monitorear / 🔴 Atención necesaria
- {knowledge_instruction}
- Empieza siempre con: "Hola {client.name}, aquí va tu resumen semanal 👋"

Además del mensaje, genera también:
- campaign_score: número entero de 0 a 100 que representa la salud general de las campañas
  * 80–100: metas siendo superadas, tendencia positiva
  * 60–79: resultados estables, sin crecimiento expresivo
  * 40–59: caída en métricas importantes, atención necesaria
  * 0–39: campañas con problema grave, acción urgente
- score_reason: una frase corta (máximo 8 palabras) justificando el score

Retorna ÚNICAMENTE un JSON válido, sin markdown, sin texto fuera del JSON:
{{"message": "...", "campaign_score": 87, "score_reason": "..."}}

Datos de esta semana:
{current}

Datos de la semana anterior (para comparación):
{previous}
"""


def generate_report_message(client, metrics: dict = None) -> dict:
    """
    Chama a API do Groq e retorna um dict com:
      - message: mensagem humanizada para o cliente
      - campaign_score: inteiro 0–100 com a saúde das campanhas
      - score_reason: frase curta justificando o score

    Se metrics não for fornecido, usa MOCK_METRICS para testes.
    Filtra as métricas pelas configurações visíveis do cliente (ClientMetricConfig).
    """
    if metrics is None:
        metrics = MOCK_METRICS

    # Filtra métricas apenas pelas visíveis configuradas pelo cliente
    try:
        visible_configs = list(client.metric_configs.filter(is_visible=True))
        if visible_configs:
            current_raw = metrics.get('current_week', {})
            previous_raw = metrics.get('previous_week', {})
            filtered: dict = {'current_week': {}, 'previous_week': {}}
            for config in visible_configs:
                p = config.platform
                k = config.metric_key
                if p not in filtered['current_week']:
                    filtered['current_week'][p] = {}
                    filtered['previous_week'][p] = {}
                curr_val = current_raw.get(p, {}).get(k)
                prev_val = previous_raw.get(p, {}).get(k)
                if curr_val is not None:
                    filtered['current_week'][p][k] = curr_val
                if prev_val is not None:
                    filtered['previous_week'][p][k] = prev_val
            metrics = filtered
    except Exception:
        logger.warning(
            "Não foi possível filtrar métricas visíveis para cliente %s. Usando métricas brutas.",
            client.id,
        )

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "user", "content": _build_prompt(client, metrics)}
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        response_text = response.json()["choices"][0]["message"]["content"]

        # Faz parse do JSON retornado pelo Groq; usa fallback em caso de falha
        try:
            parsed = json.loads(response_text)
            message = parsed["message"]
            campaign_score = int(parsed.get("campaign_score", 75))
            score_reason = parsed.get("score_reason", "")
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            logger.warning(
                "Groq não retornou JSON válido para cliente %s. Usando resposta como mensagem.",
                client.id,
            )
            message = response_text
            campaign_score = None
            score_reason = ""

        # Concatena link do dashboard público ao final da mensagem
        dashboard_url = f"{settings.BASE_URL}/dashboard/{client.dashboard_token}"
        message = f"{message}\n\nVer detalles completos → {dashboard_url}"

        return {
            "message": message,
            "campaign_score": campaign_score,
            "score_reason": score_reason,
        }
    except requests.RequestException as e:
        logger.error(
            "Erro ao chamar Groq API para cliente %s: %s",
            client.id,
            e,
            exc_info=True,
        )
        raise
