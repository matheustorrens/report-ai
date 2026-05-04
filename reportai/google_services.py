"""
Serviços de integração com Google APIs (Google Ads e GA4).
Usa REST puro com requests — sem SDK extra.
"""
import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Endpoints
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_ADS_API_VERSION = getattr(settings, 'GOOGLE_ADS_API_VERSION', 'v23')
GOOGLE_ADS_API_BASE = f'https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}'
GA4_ADMIN_API_BASE = 'https://analyticsadmin.googleapis.com/v1beta'
GA4_DATA_API_BASE = 'https://analyticsdata.googleapis.com/v1beta'


# =============================================================================
# TOKEN REFRESH
# =============================================================================

def refresh_access_token(refresh_token: str) -> dict | None:
    """
    Renova o access_token usando o refresh_token.
    Retorna dict com 'access_token' e 'expires_in', ou None em caso de erro.
    """
    if not refresh_token:
        logger.error('[google_services] refresh_token ausente')
        return None

    try:
        response = requests.post(GOOGLE_TOKEN_URL, data={
            'client_id': settings.GOOGLE_ADS_CLIENT_ID,
            'client_secret': settings.GOOGLE_ADS_CLIENT_SECRET,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'access_token': data.get('access_token'),
            'expires_in': data.get('expires_in', 3600),
        }
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro ao renovar token: {e}')
        return None


def get_valid_access_token(account) -> str | None:
    """
    Retorna um access_token válido para a IntegrationAccount.
    Renova automaticamente se expirado.
    Atualiza o model em banco.
    """
    # Verifica expiração com 5 minutos de margem
    if account.token_expiry and account.token_expiry > timezone.now() + timedelta(minutes=5):
        return account.access_token

    # Tenta renovar
    if not account.refresh_token:
        logger.warning(f'[google_services] Conta {account.id} sem refresh_token')
        return None

    result = refresh_access_token(account.refresh_token)
    if not result:
        account.status = 'token_expired'
        account.save(update_fields=['status'])
        return None

    account.access_token = result['access_token']
    account.token_expiry = timezone.now() + timedelta(seconds=result['expires_in'])
    account.save(update_fields=['access_token', 'token_expiry'])
    return account.access_token


def get_account_type(customer_id: str, refresh_token: str, access_token: str | None = None) -> dict:
    """
    Identifica se um customer_id é conta manager (MCC) ou operacional.
    Retorna: {id, is_manager, descriptive_name}
    """
    token = access_token
    if not token:
        token_result = refresh_access_token(refresh_token)
        if not token_result:
            return {
                'id': customer_id,
                'is_manager': False,
                'descriptive_name': customer_id,
            }
        token = token_result['access_token']

    developer_token = getattr(settings, 'GOOGLE_ADS_DEVELOPER_TOKEN', '')
    headers = {
        'Authorization': f'Bearer {token}',
        'developer-token': developer_token,
        'Content-Type': 'application/json',
    }

    query = """
        SELECT
            customer.id,
            customer.descriptive_name,
            customer.manager
        FROM customer
        LIMIT 1
    """

    try:
        url = f'{GOOGLE_ADS_API_BASE}/customers/{str(customer_id).replace("-", "")}/googleAds:search'
        resp = requests.post(url, headers=headers, json={'query': query}, timeout=15)
        if not resp.ok:
            logger.warning(
                f'[google_services] get_account_type HTTP {resp.status_code} para customer {customer_id}: {resp.text[:300]}'
            )
            return {
                'id': str(customer_id).replace('-', ''),
                'is_manager': False,
                'descriptive_name': str(customer_id).replace('-', ''),
            }

        results = resp.json().get('results', [])
        if not results:
            return {
                'id': str(customer_id).replace('-', ''),
                'is_manager': False,
                'descriptive_name': str(customer_id).replace('-', ''),
            }

        customer = results[0].get('customer', {})
        return {
            'id': str(customer.get('id', customer_id)).replace('-', ''),
            'is_manager': bool(customer.get('manager', False)),
            'descriptive_name': customer.get('descriptiveName') or str(customer_id).replace('-', ''),
        }
    except requests.RequestException as e:
        logger.warning(f'[google_services] Erro ao identificar tipo da conta {customer_id}: {e}')
        return {
            'id': str(customer_id).replace('-', ''),
            'is_manager': False,
            'descriptive_name': str(customer_id).replace('-', ''),
        }


def _list_manager_children(manager_customer_id: str, access_token: str) -> list[dict]:
    """Lista contas filhas diretas de uma conta MCC."""
    developer_token = getattr(settings, 'GOOGLE_ADS_DEVELOPER_TOKEN', '')
    manager_id = str(manager_customer_id).replace('-', '')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'Content-Type': 'application/json',
        'login-customer-id': manager_id,
    }

    query = """
        SELECT
            customer_client.id,
            customer_client.descriptive_name,
            customer_client.manager,
            customer_client.level
        FROM customer_client
        WHERE customer_client.level <= 1
    """

    try:
        url = f'{GOOGLE_ADS_API_BASE}/customers/{manager_id}/googleAds:search'
        resp = requests.post(url, headers=headers, json={'query': query}, timeout=20)
        if not resp.ok:
            logger.warning(
                f'[google_services] _list_manager_children HTTP {resp.status_code} para MCC {manager_id}: {resp.text[:300]}'
            )
            return []

        results = resp.json().get('results', [])
        children = []
        for row in results:
            child = row.get('customerClient', {})
            if not child:
                continue
            child_id = str(child.get('id', '')).replace('-', '')
            if not child_id:
                continue
            children.append({
                'id': child_id,
                'name': child.get('descriptiveName') or child_id,
                'is_manager': bool(child.get('manager', False)),
            })
        return children
    except requests.RequestException as e:
        logger.warning(f'[google_services] Erro ao listar filhos da MCC {manager_id}: {e}')
        return []


def discover_customer_hierarchy(refresh_token: str) -> tuple[list[dict], str | None]:
    """
    Descobre a hierarquia de contas Google Ads para o login OAuth.

    Retorna lista de dicts no formato:
    {
        id, customer_id, customer_name, is_manager, login_customer_id,
        type, currency, timezone
    }
    """
    token_result = refresh_access_token(refresh_token)
    if not token_result:
        return [], 'No se pudo renovar access token usando refresh_token.'

    access_token = token_result['access_token']
    developer_token = getattr(settings, 'GOOGLE_ADS_DEVELOPER_TOKEN', '')

    if not developer_token:
        return [], 'GOOGLE_ADS_DEVELOPER_TOKEN não configurado no .env'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'Content-Type': 'application/json',
    }

    try:
        list_url = f'{GOOGLE_ADS_API_BASE}/customers:listAccessibleCustomers'
        resp = requests.get(list_url, headers=headers, timeout=15)
        if not resp.ok:
            error_body = resp.text[:500]
            logger.error(f'[google_services] listAccessibleCustomers HTTP {resp.status_code}: {error_body}')
            return [], f'Google Ads API respondió con error {resp.status_code}: {error_body}'
        resource_names = resp.json().get('resourceNames', [])
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro ao listar contas Google Ads: {e}')
        return [], f'Error de conexión con Google Ads API: {str(e)}'

    discovered: dict[str, dict] = {}

    for resource_name in resource_names:
        customer_id = resource_name.split('/')[-1].replace('-', '')
        account_info = get_account_type(customer_id, refresh_token, access_token=access_token)

        discovered[customer_id] = {
            'id': customer_id,
            'customer_id': customer_id,
            'name': account_info.get('descriptive_name') or customer_id,
            'customer_name': account_info.get('descriptive_name') or customer_id,
            'is_manager': account_info.get('is_manager', False),
            'login_customer_id': None,
            'type': 'MANAGER' if account_info.get('is_manager', False) else 'STANDARD',
            'currency': '',
            'timezone': '',
        }

        if account_info.get('is_manager', False):
            children = _list_manager_children(customer_id, access_token)
            for child in children:
                child_id = child['id']
                if child_id == customer_id:
                    continue

                # Se a conta já for acessível diretamente, mantemos sem login_customer_id.
                existing = discovered.get(child_id)
                if existing and not existing.get('is_manager', False):
                    continue

                discovered[child_id] = {
                    'id': child_id,
                    'customer_id': child_id,
                    'name': child.get('name') or child_id,
                    'customer_name': child.get('name') or child_id,
                    'is_manager': child.get('is_manager', False),
                    'login_customer_id': customer_id,
                    'type': 'MANAGED_ACCOUNT',
                    'currency': '',
                    'timezone': '',
                }

    return list(discovered.values()), None


def build_google_ads_client(integration) -> tuple[dict | None, str | None]:
    """
    Monta configuração de cliente Google Ads por integração.
    Inclui login-customer-id apenas quando existir.
    """
    access_token = get_valid_access_token(integration)
    if not access_token:
        return None, 'token_expired'

    developer_token = getattr(settings, 'GOOGLE_ADS_DEVELOPER_TOKEN', '')
    if not developer_token:
        return None, 'GOOGLE_ADS_DEVELOPER_TOKEN não configurado no .env'

    customer_id = str(integration.customer_id or integration.account_id or '').replace('-', '')
    login_customer_id = str(integration.login_customer_id or '').replace('-', '') or None

    # Compatibilidade com registros antigos que salvaram dados em extra_data.
    if not login_customer_id:
        extra_login = (integration.extra_data or {}).get('login_customer_id')
        if extra_login:
            login_customer_id = str(extra_login).replace('-', '')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'Content-Type': 'application/json',
    }
    if login_customer_id:
        headers['login-customer-id'] = login_customer_id

    return {
        'customer_id': customer_id,
        'login_customer_id': login_customer_id,
        'headers': headers,
        'base_url': GOOGLE_ADS_API_BASE,
    }, None


# =============================================================================
# GOOGLE ADS — LISTAGEM DE CONTAS
# =============================================================================

def fetch_google_ads_accounts(access_token: str) -> tuple[list[dict], str | None]:
    """
    Retorna (lista de contas acessíveis, mensagem_de_erro ou None).
    Formato de cada conta: {id, name, currency, timezone, type}
    """
    return [], 'Use discover_customer_hierarchy(refresh_token) para Google Ads.'


# =============================================================================
# GOOGLE ADS — LISTAGEM DE CAMPANHAS
# =============================================================================

def fetch_google_ads_campaigns(account) -> tuple[list[dict], str | None]:
    """
    Retorna campanhas ativas de uma conta Google Ads via GAQL.
    Formato: [{id, name, type, status, budget}]
    Nota: Usa segments.date com último dia para retornar dados válidos.
    """
    client, error = build_google_ads_client(account)
    if error or not client:
        logger.error(f'[google_services] Falha ao montar client Google Ads para campanhas: {error}')
        return [], error or 'Falha ao montar cliente Google Ads.'

    # Query simplificada que retorna apenas campanhas, sem métricas de data
    # Usa um período recente para garantir que a API retorna dados
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.advertising_channel_type,
            campaign.status
        FROM campaign
        WHERE campaign.status IN ('ENABLED', 'PAUSED')
        ORDER BY campaign.name
        LIMIT 500
    """

    try:
        url = f"{client['base_url']}/customers/{client['customer_id']}/googleAds:search"
        resp = requests.post(url, headers=client['headers'], json={'query': query}, timeout=20)
        
        if not resp.ok:
            error_body = resp.text[:1500]
            logger.error(
                f'[google_services] Erro ao buscar campanhas da conta {account.account_id}: '
                f'HTTP {resp.status_code} - {error_body}'
            )

            api_error = f'Google Ads API respondió con error {resp.status_code}.'
            try:
                parsed = resp.json()
                details = (parsed.get('error') or {}).get('details', [])
                raw_errors = []
                request_id = None
                for detail in details:
                    request_id = request_id or detail.get('requestId')
                    raw_errors.extend(detail.get('errors', []))

                auth_errors = []
                error_messages = []
                for item in raw_errors:
                    error_code = item.get('errorCode', {})
                    auth_code = error_code.get('authorizationError')
                    if auth_code:
                        auth_errors.append(auth_code)
                    if item.get('message'):
                        error_messages.append(item['message'])

                if 'DEVELOPER_TOKEN_NOT_APPROVED' in auth_errors:
                    api_error = (
                        'DEVELOPER_TOKEN_NOT_APPROVED: tu Developer Token solo está aprobado para cuentas de prueba. '
                        'Para acceder cuentas reales, solicita acceso Basic o Standard en Google Ads API Center.'
                    )
                elif 'USER_PERMISSION_DENIED' in auth_errors:
                    api_error = (
                        'USER_PERMISSION_DENIED: la cuenta requiere login-customer-id (MCC) válido o el usuario OAuth no tiene acceso directo.'
                    )
                elif error_messages:
                    api_error = error_messages[0]

                if request_id:
                    api_error = f'{api_error} (requestId: {request_id})'
            except (ValueError, json.JSONDecodeError):
                api_error = f'{api_error} Detalle: {error_body[:300]}'

            return [], api_error
        
        results = resp.json().get('results', [])
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro de conexão ao buscar campanhas da conta {account.account_id}: {e}')
        return [], f'Error de conexión con Google Ads API: {str(e)}'
    except ValueError as e:
        logger.error(f'[google_services] Erro ao parsear resposta JSON de campanhas: {e}')
        return [], f'Error al interpretar la respuesta de Google Ads API: {str(e)}'

    campaigns = []
    for row in results:
        campaign = row.get('campaign', {})
        if campaign:
            campaigns.append({
                'id': str(campaign.get('id', '')),
                'name': campaign.get('name', ''),
                'type': campaign.get('advertisingChannelType', ''),
                'status': campaign.get('status', ''),
                'budget': 0,
            })
    
    logger.info(f'[google_services] Retornadas {len(campaigns)} campanhas da conta {account.account_id}')
    return campaigns, None


# =============================================================================
# GOOGLE ADS — MÉTRICAS
# =============================================================================

def fetch_google_ads_metrics(account, date_from: str, date_to: str, metric_keys: list[str]) -> dict:
    """
    Busca métricas reais do Google Ads para o período especificado.
    date_from / date_to: formato 'YYYY-MM-DD'
    metric_keys: lista de chaves do SelectedMetric (ex: ['impressions', 'clicks', 'cost'])
    Retorna dict com totais e dados por campanha.
    """
    client, error = build_google_ads_client(account)
    if error or not client:
        return {'error': error or 'token_expired'}

    # Mapeia chaves internas para campos GAQL
    METRIC_MAP = {
        'impressions': 'metrics.impressions',
        'clicks': 'metrics.clicks',
        'cost': 'metrics.cost_micros',
        'conversions': 'metrics.conversions',
        'conversion_value': 'metrics.conversions_value',
        'ctr': 'metrics.ctr',
        'cpc': 'metrics.average_cpc',
        'cpa': 'metrics.cost_per_conversion',
        'roas': 'metrics.value_per_conversion',
        'conversion_rate': 'metrics.conversions_from_interactions_rate',
        'avg_position': 'metrics.average_target_cpa',
        'search_impression_share': 'metrics.search_impression_share',
    }

    # Filtra apenas os campos solicitados que existem no mapa
    gaql_metrics = [METRIC_MAP[k] for k in metric_keys if k in METRIC_MAP]
    if not gaql_metrics:
        gaql_metrics = ['metrics.impressions', 'metrics.clicks', 'metrics.cost_micros']

    # Filtra por campanhas selecionadas se houver
    selected_campaign_ids = list(
        account.selected_campaigns.filter(is_active=True).values_list('campaign_id', flat=True)
    )

    campaign_filter = ''
    if selected_campaign_ids:
        ids_str = ', '.join(f"'{cid}'" for cid in selected_campaign_ids)
        campaign_filter = f"AND campaign.id IN ({ids_str})"

    fields = ', '.join(['campaign.id', 'campaign.name'] + gaql_metrics)
    query = f"""
        SELECT {fields}
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
        {campaign_filter}
        ORDER BY metrics.cost_micros DESC
    """

    try:
        url = f"{client['base_url']}/customers/{client['customer_id']}/googleAds:search"
        resp = requests.post(url, headers=client['headers'], json={'query': query}, timeout=30)
        resp.raise_for_status()
        results = resp.json().get('results', [])
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro ao buscar métricas Google Ads: {e}')
        return {'error': str(e)}

    # Processa resultados
    campaigns_data = []
    totals = {k: 0.0 for k in metric_keys}

    for row in results:
        metrics = row.get('metrics', {})
        campaign = row.get('campaign', {})

        row_data = {'campaign_id': str(campaign.get('id', '')), 'campaign_name': campaign.get('name', '')}
        for key in metric_keys:
            gaql_field = METRIC_MAP.get(key, '')
            # Converte campo GAQL para chave de acesso (ex: metrics.cost_micros → costMicros)
            field_name = gaql_field.split('.')[-1]
            field_name_camel = _to_camel(field_name)
            raw_value = metrics.get(field_name_camel, 0) or 0

            # cost_micros → dividir por 1.000.000
            if 'micros' in gaql_field:
                value = round(float(raw_value) / 1_000_000, 2)
            elif key in ('ctr', 'conversion_rate', 'search_impression_share'):
                value = round(float(raw_value) * 100, 2)  # Percentual
            else:
                value = round(float(raw_value), 2)

            row_data[key] = value
            totals[key] = round(totals.get(key, 0) + value, 2)

        campaigns_data.append(row_data)

    return {
        'totals': totals,
        'campaigns': campaigns_data,
        'date_from': date_from,
        'date_to': date_to,
    }


def _to_camel(snake_str: str) -> str:
    """Converte snake_case para camelCase."""
    parts = snake_str.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


# =============================================================================
# GA4 — LISTAGEM DE PROPRIEDADES
# =============================================================================

def fetch_ga4_properties(access_token: str) -> tuple[list[dict], str | None]:
    """
    Retorna (lista de propriedades GA4 acessíveis, mensagem_de_erro ou None).
    Formato de cada propriedade: {id, name, websiteUrl, account_name}
    """
    if not access_token:
        logger.error('[google_services] fetch_ga4_properties chamado sem access_token')
        return [], 'No se recibió token de acceso de Google. Reautoriza la integración.'

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        url = f'{GA4_ADMIN_API_BASE}/accountSummaries'
        resp = requests.get(url, headers=headers, timeout=15)
        if not resp.ok:
            error_body = resp.text[:500]
            logger.error(f'[google_services] GA4 accountSummaries HTTP {resp.status_code}: {error_body}')
            return [], f'Google Analytics API respondió con error {resp.status_code}: {error_body}'
        summaries = resp.json().get('accountSummaries', [])
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro ao listar propriedades GA4: {e}')
        return [], f'Error de conexión con Google Analytics API: {str(e)}'

    properties = []
    for account in summaries:
        for prop in account.get('propertySummaries', []):
            prop_id = prop.get('property', '').split('/')[-1]
            properties.append({
                'id': prop_id,
                'name': prop.get('displayName', prop_id),
                'websiteUrl': '',
                'account_name': account.get('displayName', ''),
            })

    return properties, None


# =============================================================================
# GA4 — MÉTRICAS
# =============================================================================

def fetch_ga4_metrics(account, date_from: str, date_to: str, metric_keys: list[str]) -> dict:
    """
    Busca métricas GA4 reais via Analytics Data API.
    date_from / date_to: formato 'YYYY-MM-DD'
    metric_keys: lista de chaves do SelectedMetric
    Retorna dict com totais.
    """
    access_token = get_valid_access_token(account)
    if not access_token:
        return {'error': 'token_expired'}

    # Mapeia chaves internas para nomes de métricas do GA4 Data API
    METRIC_MAP = {
        'sessions': 'sessions',
        'users': 'totalUsers',
        'new_users': 'newUsers',
        'pageviews': 'screenPageViews',
        'bounce_rate': 'bounceRate',
        'session_duration': 'averageSessionDuration',
        'pages_per_session': 'screenPageViewsPerSession',
        'engaged_sessions': 'engagedSessions',
        'engagement_rate': 'engagementRate',
        'events': 'eventCount',
        'conversions': 'conversions',
        'revenue': 'totalRevenue',
    }

    ga4_metrics = [{'name': METRIC_MAP[k]} for k in metric_keys if k in METRIC_MAP]
    if not ga4_metrics:
        ga4_metrics = [{'name': 'sessions'}, {'name': 'totalUsers'}]

    property_id = account.account_id
    url = f'{GA4_DATA_API_BASE}/properties/{property_id}:runReport'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    body = {
        'dateRanges': [{'startDate': date_from, 'endDate': date_to}],
        'metrics': ga4_metrics,
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f'[google_services] Erro ao buscar métricas GA4: {e}')
        return {'error': str(e)}

    # Extrai totais do primeiro (e único) row
    rows = data.get('rows', [])
    metric_headers = [m.get('name', '') for m in data.get('metricHeaders', [])]

    totals = {}
    if rows:
        values = rows[0].get('metricValues', [])
        for i, header in enumerate(metric_headers):
            # Converte de volta para chave interna
            internal_key = next((k for k, v in METRIC_MAP.items() if v == header), header)
            raw = values[i].get('value', '0') if i < len(values) else '0'
            try:
                val = float(raw)
            except ValueError:
                val = 0.0
            # Percentuais
            if internal_key in ('bounce_rate', 'engagement_rate'):
                val = round(val * 100, 2)
            else:
                val = round(val, 2)
            totals[internal_key] = val

    return {
        'totals': totals,
        'date_from': date_from,
        'date_to': date_to,
    }
