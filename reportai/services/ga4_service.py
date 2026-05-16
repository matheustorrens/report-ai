"""
Servico GA4: busca metricas semanais para o fluxo de geracao de relatorio.
Wrapper fino sobre fetch_ga4_metrics ja existente em google_services.py.
Retorna o mesmo formato do MOCK_METRICS para que o Groq receba dados compativeis.
"""
import logging
from datetime import date, timedelta

from reportai.google_services import fetch_ga4_metrics

logger = logging.getLogger(__name__)

# Todas as chaves de métricas GA4 suportadas (correspondem a SelectedMetric.GA4_METRICS)
GA4_METRIC_KEYS = [
    'sessions', 'users', 'new_users', 'pageviews', 'bounce_rate',
    'session_duration', 'pages_per_session', 'engaged_sessions',
    'engagement_rate', 'events', 'conversions', 'revenue',
]


def _date_range(weeks_back: int) -> tuple[str, str]:
    """
    Retorna (date_from, date_to) no formato 'YYYY-MM-DD'.
    weeks_back=0 -> semana atual (ultimos 7 dias, terminando ontem)
    weeks_back=1 -> semana anterior (8 a 14 dias atras)
    """
    today = date.today()
    end = today - timedelta(days=1 + weeks_back * 7)
    start = end - timedelta(days=6)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


def get_weekly_metrics(client) -> dict | None:
    """
    Retorna metricas GA4 das ultimas 2 semanas para o cliente.
    Retorna None se o cliente nao tiver integracao GA4 ativa -- o caller usa MOCK_METRICS.

    Formato de retorno (compativel com MOCK_METRICS do groq_service):
    {
        "current_week":  {"ga4": {"sessions": N, "users": N, "bounce_rate": N, "avg_session_duration": N}},
        "previous_week": {"ga4": {...}},
    }
    """
    # Busca a primeira integracao GA4 conectada do cliente
    integration = (
        client.integrations
        .filter(channel='ga4', status='connected')
        .first()
    )
    if not integration:
        logger.info('[ga4_service] Nenhuma integracao GA4 ativa para cliente %s', client.id)
        return None

    current_from, current_to = _date_range(0)
    previous_from, previous_to = _date_range(1)

    current_raw = fetch_ga4_metrics(integration, current_from, current_to, GA4_METRIC_KEYS)
    previous_raw = fetch_ga4_metrics(integration, previous_from, previous_to, GA4_METRIC_KEYS)

    if 'error' in current_raw:
        logger.error('[ga4_service] Erro ao buscar metricas atuais GA4: %s', current_raw['error'])
        return None

    if 'error' in previous_raw:
        logger.warning(
            '[ga4_service] Erro ao buscar metricas semana anterior GA4 (usando zeros): %s',
            previous_raw['error'],
        )
        previous_raw = {'totals': {}}

    def _build_ga4_dict(totals: dict) -> dict:
        """Passa todos os totais do fetch_ga4_metrics sem renomear — as chaves já
        correspondem exatamente aos metric_key do ClientMetricConfig."""
        return dict(totals)

    return {
        'current_week': {
            'ga4': _build_ga4_dict(current_raw.get('totals', {})),
        },
        'previous_week': {
            'ga4': _build_ga4_dict(previous_raw.get('totals', {})),
        },
    }
