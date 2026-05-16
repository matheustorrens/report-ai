"""
Serviço Google Ads: busca métricas semanais para o fluxo de geração de relatório.
Wrapper fino sobre fetch_google_ads_metrics já existente em google_services.py.
Retorna o mesmo formato do MOCK_METRICS para que o Groq receba dados compatíveis.
Agrega múltiplas contas Google Ads do mesmo cliente quando necessário.
"""
import logging
from datetime import date, timedelta

from reportai.google_services import fetch_google_ads_metrics

logger = logging.getLogger(__name__)

# Métricas brutas (absolutas) — somadas entre contas
_SUM_KEYS = ['clicks', 'impressions', 'cost', 'conversions', 'conversion_value']

# Métricas de taxa — calculadas a partir dos totais somados
_RATE_KEYS = ['ctr', 'cpc', 'cpa', 'roas']

# Todas as métricas solicitadas à Google Ads API
GOOGLE_ADS_METRIC_KEYS = _SUM_KEYS + _RATE_KEYS


def _date_range(weeks_back: int) -> tuple[str, str]:
    """
    Retorna (date_from, date_to) no formato 'YYYY-MM-DD'.
    weeks_back=0 → semana atual (últimos 7 dias, terminando ontem)
    weeks_back=1 → semana anterior (8 a 14 dias atrás)
    """
    today = date.today()
    end = today - timedelta(days=1 + weeks_back * 7)
    start = end - timedelta(days=6)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


def _recompute_rates(totals: dict) -> dict:
    """
    Recalcula métricas de taxa (CTR, CPC, CPA, ROAS) a partir dos totais somados.
    Evita divisão por zero retornando 0.0 quando o denominador é zero.
    """
    clicks = totals.get('clicks', 0) or 0
    impressions = totals.get('impressions', 0) or 0
    cost = totals.get('cost', 0) or 0
    conversions = totals.get('conversions', 0) or 0
    conversion_value = totals.get('conversion_value', 0) or 0

    totals['ctr'] = round((clicks / impressions * 100), 4) if impressions > 0 else 0.0
    totals['cpc'] = round(cost / clicks, 4) if clicks > 0 else 0.0
    totals['cpa'] = round(cost / conversions, 4) if conversions > 0 else 0.0
    totals['roas'] = round(conversion_value / cost, 4) if cost > 0 else 0.0
    # Alias para retrocompatibilidade com DEFAULT_METRICS que usa 'spend'
    totals['spend'] = totals.get('cost', 0.0)
    return totals


def _aggregate_week(integrations: list, date_from: str, date_to: str) -> dict | None:
    """
    Agrega métricas de todas as contas Google Ads do cliente em uma semana.
    Retorna None se nenhuma conta retornar dados válidos.
    """
    combined = {k: 0.0 for k in _SUM_KEYS}
    any_data = False

    for integration in integrations:
        raw = fetch_google_ads_metrics(
            integration, date_from, date_to, GOOGLE_ADS_METRIC_KEYS
        )
        if 'error' in raw:
            logger.warning(
                '[google_ads_service] Erro na conta %s: %s',
                integration.account_id,
                raw['error'],
            )
            continue

        totals = raw.get('totals', {})
        any_data = True
        for k in _SUM_KEYS:
            combined[k] = round(combined[k] + float(totals.get(k, 0) or 0), 2)

    if not any_data:
        return None

    return _recompute_rates(combined)


def get_weekly_metrics(client) -> dict | None:
    """
    Retorna métricas Google Ads das últimas 2 semanas para o cliente.
    Retorna None se o cliente não tiver integração Google Ads ativa — o caller usa MOCK_METRICS.

    Formato de retorno (compatível com MOCK_METRICS do groq_service):
    {
        "current_week":  {"google_ads": {"clicks": N, "impressions": N, "cost": N, ...}},
        "previous_week": {"google_ads": {...}},
    }
    """
    integrations = list(
        client.integrations.filter(channel='google_ads', status='connected')
    )
    if not integrations:
        logger.info(
            '[google_ads_service] Nenhuma integração Google Ads ativa para cliente %s',
            client.id,
        )
        return None

    current_from, current_to = _date_range(0)
    previous_from, previous_to = _date_range(1)

    current_totals = _aggregate_week(integrations, current_from, current_to)
    if current_totals is None:
        logger.error(
            '[google_ads_service] Nenhuma conta retornou dados para cliente %s', client.id
        )
        return None

    previous_totals = _aggregate_week(integrations, previous_from, previous_to)
    if previous_totals is None:
        logger.warning(
            '[google_ads_service] Semana anterior sem dados para cliente %s — usando zeros',
            client.id,
        )
        previous_totals = {k: 0.0 for k in GOOGLE_ADS_METRIC_KEYS}

    return {
        'current_week': {'google_ads': current_totals},
        'previous_week': {'google_ads': previous_totals},
    }
