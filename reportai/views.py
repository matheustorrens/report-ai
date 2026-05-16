import json
import secrets
import uuid as uuid_module
from datetime import timedelta
from types import SimpleNamespace
from urllib.parse import urlencode

from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

import requests

from .models import Client, IntegrationAccount, SelectedCampaign, SelectedMetric, ReportLog, ClientMetricConfig, TimelineEntry, AgencyProfile
from .services.groq_service import generate_report_message, MOCK_METRICS
from .services.email_service import send_report_email
from .services.ga4_service import get_weekly_metrics as get_ga4_metrics
from .services.google_ads_service import get_weekly_metrics as get_google_ads_metrics
from .google_services import (
    discover_customer_hierarchy,
    fetch_google_ads_campaigns,
    fetch_google_ads_metrics,
    fetch_ga4_properties,
    fetch_ga4_metrics,
    get_valid_access_token,
)


# ============================================================
# API ENDPOINTS - Google Ads y GA4
# ============================================================

# Google OAuth2 endpoints
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_ADS_API_URL = 'https://googleads.googleapis.com/v15'
GA4_API_URL = 'https://analyticsadmin.googleapis.com/v1beta'

# Meta/Facebook OAuth endpoints
META_AUTH_URL = 'https://www.facebook.com/v18.0/dialog/oauth'
META_TOKEN_URL = 'https://graph.facebook.com/v18.0/oauth/access_token'
META_API_URL = 'https://graph.facebook.com/v18.0'

# OAuth scopes
GOOGLE_ADS_SCOPE = 'https://www.googleapis.com/auth/adwords'
GA4_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'
META_ADS_SCOPE = 'ads_management,ads_read,business_management'


# ============================================================
# UTILITÁRIOS LOCAIS
# ============================================================

def _clean_phone(val):
    """Normaliza número de telefone: mantém + inicial, remove tudo que não é dígito."""
    if not val:
        return ''
    s = val.strip()
    prefix = '+' if s.startswith('+') else ''
    return prefix + ''.join(c for c in s if c.isdigit())


# ============================================================
# AUTH VIEWS
# ============================================================

def login_view(request):
    """Login: GET renderiza o form, POST autentica e redireciona."""
    if request.user.is_authenticated:
        return redirect('reportai:dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        # Django usa username internamente; tentamos pelo email
        from django.contrib.auth import authenticate, login as auth_login
        from django.contrib.auth.models import User
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            auth_login(request, user)
            return redirect('reportai:dashboard')
        else:
            return render(request, 'reportai/auth/login.html', {'error': 'Email o contraseña incorrectos.'})
    return render(request, 'reportai/auth/login.html')


def register_view(request):
    """Registro: GET renderiza o form, POST cria usuário, faz login e redireciona."""
    if request.user.is_authenticated:
        return redirect('reportai:dashboard')
    if request.method == 'POST':
        from django.contrib.auth import login as auth_login
        from django.contrib.auth.models import User
        agency_name = request.POST.get('agency_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        error = None
        if not agency_name:
            error = 'El nombre de la agencia es requerido.'
        elif not email or '@' not in email:
            error = 'Introduce un email válido.'
        elif len(password) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        elif password != password_confirm:
            error = 'Las contraseñas no coinciden.'
        elif User.objects.filter(email=email).exists():
            error = 'Ya existe una cuenta con ese email.'
        if error:
            return render(request, 'reportai/auth/register.html', {'error': error})
        # Cria o usuário usando o email como username (único)
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=agency_name,
        )
        # Registra os timestamps de aceite dos documentos legais no momento do registro
        profile, _ = AgencyProfile.objects.get_or_create(user=user)
        now = timezone.now()
        profile.terms_accepted_at = now
        profile.privacy_accepted_at = now
        profile.legal_version = "1.0"
        profile.save()
        auth_login(request, user)
        return redirect('reportai:dashboard')
    return render(request, 'reportai/auth/register.html')


def onboarding_view(request):
    """Onboarding flow after registration."""
    return render(request, 'reportai/auth/onboarding.html')


def logout_view(request):
    """Logout e redireciona para login."""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect('reportai:login')


@login_required
def agency_profile_view(request):
    """Página de configuração do perfil da agência: nome, email e WhatsApp."""
    user = request.user
    profile, _ = AgencyProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        agency_name = request.POST.get('agency_name', '').strip()
        email = request.POST.get('email', '').strip()
        whatsapp = _clean_phone(request.POST.get('whatsapp', ''))

        error = None
        if not agency_name:
            error = 'El nombre de la agencia es obligatorio.'
        elif not email or '@' not in email:
            error = 'Introduce un email válido.'

        if error:
            return render(request, 'reportai/agency/profile.html', {
                'active_nav': 'profile',
                'error': error,
                'agency_name': agency_name,
                'email': email,
                'whatsapp': whatsapp,
            })

        # Verifica se email já está em uso por outro usuário
        from django.contrib.auth.models import User as AuthUser
        if AuthUser.objects.filter(email=email).exclude(pk=user.pk).exists():
            return render(request, 'reportai/agency/profile.html', {
                'active_nav': 'profile',
                'error': 'Este email ya está en uso por otra cuenta.',
                'agency_name': agency_name,
                'email': email,
                'whatsapp': whatsapp,
            })

        user.first_name = agency_name
        user.email = email
        user.save(update_fields=['first_name', 'email'])

        profile.whatsapp = whatsapp
        profile.save(update_fields=['whatsapp'])

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('reportai:agency_profile')

    return render(request, 'reportai/agency/profile.html', {
        'active_nav': 'profile',
        'agency_name': user.first_name,
        'email': user.email,
        'whatsapp': profile.whatsapp,
    })


# ============================================================
# DASHBOARD VIEW
# ============================================================

@login_required
def dashboard_view(request):
    """Página principal do dashboard com dados reais do banco."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    # Totais gerais
    total_clients = Client.objects.filter(owner=request.user).count()
    report_stats = ReportLog.objects.filter(client__owner=request.user).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
    )
    total_reports = report_stats['total']
    sent_reports = report_stats['sent']
    failed_reports = report_stats['failed']

    # Cálculo de tendências — compara últimos 7 dias com os 7 dias anteriores
    def _pct_delta(current, previous):
        """Retorna (valor_formatado, é_positivo) para o template."""
        if previous == 0:
            return ('+100' if current > 0 else '0'), current > 0
        delta = round((current - previous) / previous * 100)
        sign = '+' if delta >= 0 else ''
        return f'{sign}{delta}', delta >= 0

    stats_this = ReportLog.objects.filter(
        client__owner=request.user, sent_at__gte=week_ago
    ).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
    )
    stats_prev = ReportLog.objects.filter(
        client__owner=request.user,
        sent_at__gte=two_weeks_ago, sent_at__lt=week_ago,
    ).aggregate(
        total=Count('id'),
        sent=Count('id', filter=Q(status='sent')),
    )
    clients_this_week = Client.objects.filter(
        owner=request.user, created_at__gte=week_ago
    ).count()
    clients_prev_week = Client.objects.filter(
        owner=request.user,
        created_at__gte=two_weeks_ago, created_at__lt=week_ago,
    ).count()

    trend_reports_val, trend_reports_pos = _pct_delta(stats_this['total'], stats_prev['total'])
    trend_sent_val, trend_sent_pos = _pct_delta(stats_this['sent'], stats_prev['sent'])
    trend_clients_val, trend_clients_pos = _pct_delta(clients_this_week, clients_prev_week)

    # Clientes com relatórios falhados na última semana para o painel de revisão
    needs_attention = (
        ReportLog.objects
        .filter(client__owner=request.user, status='failed', sent_at__gte=week_ago)
        .select_related('client')
        .order_by('-sent_at')[:5]
    )
    # Próximos envíos: calcula candidato por cliente e ordena por data
    clients_qs = Client.objects.filter(owner=request.user)
    upcoming = []
    for client in clients_qs:
        candidate_date = None
        if client.next_report_at:
            candidate_date = client.next_report_at
        else:
            last_log = ReportLog.objects.filter(client=client).order_by('-sent_at').first()
            if last_log and client.report_frequency_days:
                candidate_date = last_log.sent_at + timedelta(days=client.report_frequency_days)
        if candidate_date:
            upcoming.append({'client': client, 'date': candidate_date})
    upcoming_reports = sorted(upcoming, key=lambda x: x['date'])[:5]
    next_report = upcoming_reports[0] if upcoming_reports else None
    # Últimos 5 relatórios enviados para o painel esquerdo
    recent_reports = (
        ReportLog.objects
        .filter(client__owner=request.user)
        .select_related('client')
        .order_by('-sent_at')[:5]
    )
    context = {
        'total_clients': total_clients,
        'total_reports': total_reports,
        'sent_reports': sent_reports,
        'failed_reports': failed_reports,
        'trend_reports_val': trend_reports_val,
        'trend_reports_pos': trend_reports_pos,
        'trend_sent_val': trend_sent_val,
        'trend_sent_pos': trend_sent_pos,
        'trend_clients_val': trend_clients_val,
        'trend_clients_pos': trend_clients_pos,
        'needs_attention': needs_attention,
        'next_report': next_report,
        'upcoming_reports': upcoming_reports,
        'recent_reports': recent_reports,
        'active_nav': 'dashboard',
    }
    return render(request, 'reportai/dashboard.html', context)


# ============================================================
# CLIENTS VIEWS
# ============================================================

@login_required
def clients_list_view(request):
    """Lista de todos os clientes com status de integração."""
    clients = Client.objects.filter(owner=request.user).prefetch_related('integrations')
    
    # Usa o cache do prefetch_related filtrando em Python — evita N+1 queries
    clients_data = []
    for client in clients:
        all_integrations = client.integrations.all()  # usa cache, sem query adicional
        connected_channels = {i.channel for i in all_integrations if i.status == 'connected'}
        integrations = {
            'google_ads': 'google_ads' in connected_channels,
            'ga4': 'ga4' in connected_channels,
            'meta_ads': 'meta_ads' in connected_channels,
        }
        clients_data.append({
            'client': client,
            'integrations': integrations,
            'integration_count': len(connected_channels),
        })
    
    context = {
        'clients_data': clients_data,
        'total_clients': len(clients_data),
        'active_nav': 'clients',
    }
    return render(request, 'reportai/clients/list.html', context)


def client_create_view(request):
    """Redireciona para lista de clientes — criação ocorre via modal AJAX em list.html."""
    return redirect('reportai:clients')


@login_required
def client_profile_view(request, client_id):
    """Perfil individual do cliente com integrações reais e histórico de relatórios."""
    client = get_object_or_404(Client, id=client_id, owner=request.user)

    # Uma única query busca todas as integrações; filtra em Python (evita 4 queries separadas)
    all_integrations = list(client.integrations.all())
    integrations = {
        'google_ads': next((i for i in all_integrations if i.channel == 'google_ads'), None),
        'ga4':        next((i for i in all_integrations if i.channel == 'ga4'), None),
        'meta_ads':   next((i for i in all_integrations if i.channel == 'meta_ads'), None),
    }
    connected_channels = {i.channel for i in all_integrations if i.status == 'connected'}

    # Histórico real de relatórios deste cliente
    recent_logs = (
        ReportLog.objects
        .filter(client=client)
        .order_by('-sent_at')[:20]
    )

    # Iniciais do nome do cliente para o avatar
    initials = ''.join(w[0] for w in client.name.split()[:2]).upper()

    # Métricas agrupadas por plataforma — apenas para canais conectados
    PLATFORM_LABELS = {
        'google_ads': 'Google Ads',
        'ga4': 'Google Analytics 4',
        'meta_ads': 'Meta Ads',
    }
    platforms = {}
    for config in client.metric_configs.all():
        p = config.platform
        if p not in connected_channels:
            continue
        if p not in platforms:
            platforms[p] = {'label': PLATFORM_LABELS.get(p, p), 'metrics': []}
        platforms[p]['metrics'].append(config)
    
    # Detecta onboarding: ?onboarding=1 abre modal pós-cadastro
    show_onboarding = request.GET.get('onboarding') == '1'

    # Entradas da timeline para a nova aba
    timeline_entries = client.timeline_entries.all()
    
    context = {
        'client': client,
        'integrations': integrations,
        'recent_logs': recent_logs,
        'client_initials': initials,
        'connected_channels': connected_channels,
        'platforms': platforms,
        'show_onboarding': show_onboarding,
        'timeline_entries': timeline_entries,
        'active_nav': 'clients',
    }
    return render(request, 'reportai/clients/profile.html', context)


def client_edit_view(request, client_id):
    """Redireciona para lista de clientes — edição ocorre via modal AJAX em list.html."""
    return redirect('reportai:clients')


def client_delete_view(request, client_id):
    """Delete a client."""
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, f'Cliente "{client.name}" eliminado correctamente.')
    return redirect('reportai:clients')


@login_required
@require_http_methods(["GET", "POST"])
def client_metrics_config_view(request, client_id):
    """
    Configura quais métricas aparecem no dashboard público do cliente.
    GET: exibe o formulário de configuração por plataforma.
    POST: salva as alterações de is_visible, display_name e order.
    Restringe acesso ao owner do cliente (isolamento multi-tenant).
    """
    client = get_object_or_404(Client, id=client_id, owner=request.user)

    if request.method == 'POST':
        # Coleta alterações e usa bulk_update — 1 UPDATE no lugar de N saves individuais
        configs_to_update = []
        for config in client.metric_configs.all():
            field_prefix = f"metric_{config.id}"
            config.is_visible = f"{field_prefix}_visible" in request.POST
            display_name = request.POST.get(f"{field_prefix}_name", config.display_name).strip()
            if display_name:
                config.display_name = display_name
            try:
                config.order = int(request.POST.get(f"{field_prefix}_order", config.order))
            except (ValueError, TypeError):
                pass
            configs_to_update.append(config)
        if configs_to_update:
            ClientMetricConfig.objects.bulk_update(
                configs_to_update, ['is_visible', 'display_name', 'order']
            )
        messages.success(request, 'Configuración de métricas guardada.')
        # Se veio do perfil do cliente, redireciona de volta para a aba de métricas
        next_url = request.POST.get('next', '')
        if next_url.startswith('/app/clients/'):
            return redirect(next_url)
        return redirect('reportai:client_metrics_config', client_id=client_id)

    # Agrupa métricas por plataforma para o template
    PLATFORM_LABELS = {
        'google_ads': 'Google Ads',
        'ga4': 'Google Analytics 4',
        'meta_ads': 'Meta Ads',
    }
    platforms = {}
    for config in client.metric_configs.all():
        p = config.platform
        if p not in platforms:
            platforms[p] = {'label': PLATFORM_LABELS.get(p, p), 'metrics': []}
        platforms[p]['metrics'].append(config)

    context = {
        'client': client,
        'platforms': platforms,
        'active_nav': 'clients',
    }
    return render(request, 'reportai/clients/metrics_config.html', context)


@login_required
@require_POST
def api_create_client(request):
    """API endpoint to create a new client."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = _clean_phone(data.get('phone', ''))
        company = data.get('company', '').strip()
        knowledge_level = data.get('knowledge_level', 'leigo')
        if knowledge_level not in ('leigo', 'avancado'):
            knowledge_level = 'leigo'
        
        if not name:
            return JsonResponse({'error': 'El nombre del cliente es requerido.'}, status=400)
        if len(name) > 30:
            return JsonResponse({'error': 'El nombre del cliente no puede superar los 30 caracteres.'}, status=400)
        if company and len(company) > 20:
            return JsonResponse({'error': 'El nombre de la empresa no puede superar los 20 caracteres.'}, status=400)
        
        owner = request.user
        
        # Verifica se a agência já aceitou o DPA antes de criar o primeiro cliente
        is_first_client = not Client.objects.filter(owner=owner).exists()
        if is_first_client:
            profile, _ = AgencyProfile.objects.get_or_create(user=owner)
            if profile.dpa_accepted_at is None:
                return JsonResponse({
                    'error': 'dpa_required',
                    'message': 'Debes aceptar el Acuerdo de Encargo de Tratamiento (DPA) antes de añadir tu primer cliente.',
                    'dpa_url': reverse('dpa'),
                }, status=403)
        
        client = Client.objects.create(
            name=name,
            email=email if email else None,
            phone=phone if phone else None,
            company=company if company else None,
            knowledge_level=knowledge_level,
            owner=owner
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente "{name}" creado correctamente.',
            'client': {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'company': client.company,
            },
            'profile_url': reverse('reportai:client_profile', args=[client.id]) + '?onboarding=1',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_accept_dpa(request):
    """Endpoint para registrar o aceite do DPA pela agência com timestamp."""
    profile, _ = AgencyProfile.objects.get_or_create(user=request.user)
    if profile.dpa_accepted_at is None:
        profile.dpa_accepted_at = timezone.now()
        profile.legal_version = "1.0"
        profile.save(update_fields=['dpa_accepted_at', 'legal_version'])
    return JsonResponse({'success': True, 'dpa_accepted_at': profile.dpa_accepted_at.isoformat()})


@login_required
@require_POST
def api_update_client(request, client_id):
    """API endpoint to update a client."""
    try:
        client = get_object_or_404(Client, id=client_id, owner=request.user)
        data = json.loads(request.body)

        # Campos de texto: só atualiza se vier no payload
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return JsonResponse({'error': 'El nombre del cliente es requerido.'}, status=400)
            if len(name) > 30:
                return JsonResponse({'error': 'El nombre del cliente no puede superar los 30 caracteres.'}, status=400)
            client.name = name

        if 'knowledge_level' in data:
            knowledge_level = data['knowledge_level']
            if knowledge_level not in ('leigo', 'avancado'):
                knowledge_level = 'leigo'
            client.knowledge_level = knowledge_level

        if 'email' in data:
            client.email = data['email'].strip() or None
        if 'phone' in data:
            client.phone = _clean_phone(data['phone']) or None
        if 'company' in data:
            company_val = data['company'].strip()
            if company_val and len(company_val) > 20:
                return JsonResponse({'error': 'El nombre de la empresa no puede superar los 20 caracteres.'}, status=400)
            client.company = company_val or None

        # Novos campos de frequência de envio
        if 'report_frequency' in data:
            valid_frequencies = [c[0] for c in Client.FREQUENCY_CHOICES]
            if data['report_frequency'] in valid_frequencies:
                client.report_frequency = data['report_frequency']
        if 'report_send_day' in data:
            try:
                report_send_day = int(data['report_send_day'])
                if 0 <= report_send_day <= 28:
                    client.report_send_day = report_send_day
            except (ValueError, TypeError):
                pass

        client.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente "{client.name}" actualizado correctamente.',
            'client': {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'company': client.company,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_delete_client(request, client_id):
    """API endpoint to delete a client."""
    try:
        client = get_object_or_404(Client, id=client_id, owner=request.user)
        client_name = client.name
        client.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente "{client_name}" eliminado correctamente.',
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# REPORTS VIEWS
# ============================================================

@login_required
def reports_list_view(request):
    """Histórico de relatórios enviados."""
    logs = (
        ReportLog.objects.filter(client__owner=request.user)
        .select_related('client')
        .order_by('-sent_at')[:50]
    )
    return render(request, 'reportai/reports/list.html', {'logs': logs, 'active_nav': 'reports'})


@login_required
def report_generate_view(request):
    """Formulário de geração de relatório com preview."""
    clients = Client.objects.filter(owner=request.user)
    # Passa o WhatsApp da agência para o template (usado no botão wa.me)
    profile, _ = AgencyProfile.objects.get_or_create(user=request.user)
    return render(request, 'reportai/reports/generate.html', {
        'clients': clients,
        'active_nav': 'reports',
        'agency_whatsapp': profile.whatsapp,
    })


@require_POST
def api_report_preview(request):
    """Gera preview da mensagem via Groq sem enviar por nenhum canal.
    Aceita metrics_override no payload para usar métricas editadas temporariamente.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'success': False, 'error': 'client_id obrigatório.'}, status=400)

    client = get_object_or_404(Client, id=client_id)

    # Parâmetros de período (aceita days ou period_start+period_end para uso futuro com APIs reais)
    days = data.get('days')
    period_start = data.get('period_start')
    period_end = data.get('period_end')

    # Chaves de métricas selecionadas pelos chips — sobrescreve o filtro is_visible do DB
    selected_metric_keys = data.get('selected_metric_keys')  # {platform: [key1, key2]}

    try:
        metrics_override = data.get('metrics_override')  # dict legado: {platform: {key: val}}
        if metrics_override and isinstance(metrics_override, dict):
            # Usa os valores editados como current_week; previous_week vem do MOCK
            metrics = {
                'current_week': metrics_override,
                'previous_week': MOCK_METRICS.get('previous_week', {}),
            }
            data_source = 'override'
        else:
            # Busca métricas reais de GA4 e Google Ads — usa MOCK apenas se nenhum retornar dados
            ga4_data  = get_ga4_metrics(client)
            gads_data = get_google_ads_metrics(client)

            if ga4_data or gads_data:
                metrics = {'current_week': {}, 'previous_week': {}}
                for week in ('current_week', 'previous_week'):
                    if ga4_data:
                        metrics[week].update(ga4_data.get(week, {}))
                    if gads_data:
                        metrics[week].update(gads_data.get(week, {}))
                sources = [s for s, d in (('ga4', ga4_data), ('google_ads', gads_data)) if d]
                data_source = '+'.join(sources)
            else:
                metrics = None
                data_source = 'mock'

        result = generate_report_message(client, metrics=metrics, selected_keys=selected_metric_keys)
        # URL do dashboard público do cliente — o JS appenda ao final da mensagem de preview
        dashboard_url = request.build_absolute_uri(f'/dashboard/{client.dashboard_slug}/')
        return JsonResponse({
            'success': True,
            'message': result['message'],
            'dashboard_insight': result.get('dashboard_insight', ''),
            'campaign_score': result.get('campaign_score'),
            'score_reason': result.get('score_reason', ''),
            'data_source': data_source,
            'dashboard_url': dashboard_url,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def api_report_send(request):
    """Envia o relatório e cria um ReportLog com o resultado."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    client_id = data.get('client_id')
    message = data.get('message', '').strip()

    if not client_id or not message:
        return JsonResponse(
            {'success': False, 'error': 'client_id e message são obrigatórios.'}, status=400
        )

    client = get_object_or_404(Client, id=client_id)

    # Combina GA4 + Google Ads (igual ao api_report_preview) para o snapshot
    ga4_data  = get_ga4_metrics(client)
    gads_data = get_google_ads_metrics(client)
    if ga4_data or gads_data:
        metrics_snapshot: dict = {'current_week': {}, 'previous_week': {}}
        for week in ('current_week', 'previous_week'):
            if ga4_data:
                metrics_snapshot[week].update(ga4_data.get(week, {}))
            if gads_data:
                metrics_snapshot[week].update(gads_data.get(week, {}))
    else:
        # Copia rasa do MOCK para não poluir o global entre requisições
        metrics_snapshot = {**MOCK_METRICS}

    # Métricas escolhidas como destaque no momento de gerar o relatório
    highlighted = data.get('highlighted_metrics', [])
    if isinstance(highlighted, list):
        clean = []
        for item in highlighted[:6]:
            if isinstance(item, dict) and 'key' in item and 'platform' in item:
                clean.append({'key': str(item['key']), 'platform': str(item['platform'])})
            elif isinstance(item, str):
                # Retrocompatibilidade: string plana de snapshots antigos
                clean.append(item)
        highlighted = clean
    else:
        highlighted = []
    metrics_snapshot['highlighted'] = highlighted

    # Insight do dashboard gerado na etapa de preview e repassado pelo frontend
    dashboard_insight = str(data.get('dashboard_insight', ''))[:5000]

    # Score gerado na etapa de preview e repassado pelo frontend
    campaign_score_raw = data.get('campaign_score')
    try:
        campaign_score = int(campaign_score_raw) if campaign_score_raw is not None else None
    except (ValueError, TypeError):
        campaign_score = None
    score_reason = str(data.get('score_reason', ''))[:120]

    log = ReportLog(
        client=client,
        message_generated=message,
        dashboard_insight=dashboard_insight,
        channel_used=client.send_channel,
        metrics_snapshot=metrics_snapshot,
        campaign_score=campaign_score,
        score_reason=score_reason,
    )

    errors = []
    email_ok = None
    whatsapp_ok = None

    # O `message` recebido do frontend já contém o link do dashboard (appendado no preview pelo JS).
    # Não há necessidade de adicionar novamente aqui — evita duplicação.

    if client.send_channel in ('email', 'both'):
        if not client.email:
            email_ok = 'failed'
            errors.append('Email: cliente sem e-mail cadastrado.')
        else:
            try:
                # Identidade da agência: nome visível como remetente, email como reply-to
                agency_name = client.owner.first_name or client.owner.username
                agency_email = client.owner.email
                send_report_email(
                    client.email,
                    client.name,
                    message,
                    agency_name=agency_name,
                    agency_email=agency_email,
                )
                email_ok = 'sent'
            except Exception as e:
                email_ok = 'failed'
                errors.append(f'Email: {e}')

    # WhatsApp é enviado via link wa.me aberto no browser do usuário (frontend).
    # Não há envio automático pelo backend — nenhuma API de terceiro processa dados aqui.

    log.email_status = email_ok
    log.whatsapp_status = whatsapp_ok
    log.error_detail = '; '.join(errors) if errors else None

    statuses = [s for s in (email_ok, whatsapp_ok) if s is not None]
    if all(s == 'sent' for s in statuses):
        log.status = 'sent'
    elif any(s == 'sent' for s in statuses):
        log.status = 'partial'
    else:
        log.status = 'failed'

    log.save()

    return JsonResponse({
        'success': log.status != 'failed',
        'status': log.status,
        'errors': errors,
        'log_id': log.id,
    })


def api_client_report_config(request, client_id):
    """Retorna a configuração de relatório do cliente para preencher o formulário via AJAX."""
    client = get_object_or_404(Client, id=client_id)
    return JsonResponse({
        'knowledge_level': client.knowledge_level,
        'send_channel': client.send_channel,
        'report_frequency_days': client.report_frequency_days,
        'report_frequency': client.report_frequency,
        'report_send_day': client.report_send_day,
        'has_email': bool(client.email),
        'has_phone': bool(client.phone),
        'phone': client.phone or '',
    })


@login_required
@require_GET
def api_client_metrics(request, client_id):
    """
    Retorna as métricas do cliente agrupadas por plataforma.
    Usado pelo generate.html para pré-carregar o painel de métricas editáveis.
    Apenas plataformas com IntegrationAccount status='connected' são incluídas.
    """
    client = get_object_or_404(Client, id=client_id, owner=request.user)

    # Apenas plataformas que têm integração realmente conectada
    connected_platforms = set(
        client.integrations.filter(status='connected').values_list('channel', flat=True)
    )

    configs = (
        client.metric_configs
        .filter(platform__in=connected_platforms)
        .order_by('platform', 'order')
    )

    data: dict = {}

    for config in configs:
        p = config.platform
        if p not in data:
            data[p] = []
        data[p].append({
            'id': config.id,
            'metric_key': config.metric_key,
            'display_name': config.display_name,
            'order': config.order,
            'is_visible': config.is_visible,
        })

    return JsonResponse({'metrics': data})


# ============================================================
# INTEGRATIONS VIEWS - FLUJO PRINCIPAL
# ============================================================

@login_required
def integrations_view(request):
    """
    Página principal de gestión de integraciones.
    
    Flujo:
    1. Seleccionar cliente
    2. Ver todas las cuentas de integración del cliente (agrupadas por canal)
    3. Conectar nuevas cuentas o gestionar existentes
    """
    clients = Client.objects.filter(owner=request.user)
    
    # Get selected client from query param
    selected_client_id = request.GET.get('client_id')
    selected_client = None
    integrations_by_channel = {}
    
    if selected_client_id:
        try:
            selected_client = Client.objects.get(id=selected_client_id, owner=request.user)

            # Uma única query busca todas as contas do cliente com prefetch;
            # agrupa e conta em Python (evita loop de 9 queries)
            all_accounts = list(
                IntegrationAccount.objects
                .filter(client=selected_client)
                .prefetch_related('selected_campaigns', 'selected_metrics')
            )
            accounts_by_channel: dict = {}
            for acc in all_accounts:
                accounts_by_channel.setdefault(acc.channel, []).append(acc)

            for channel, channel_name in IntegrationAccount.CHANNEL_CHOICES:
                channel_accs = accounts_by_channel.get(channel, [])
                integrations_by_channel[channel] = {
                    'name': channel_name,
                    'accounts': channel_accs,
                    'count': sum(1 for a in channel_accs if a.status == 'connected'),
                    'pending_count': sum(1 for a in channel_accs if a.status == 'pending_selection'),
                }

        except Client.DoesNotExist:
            messages.error(request, 'Cliente no encontrado.')
    
    context = {
        'clients': clients,
        'selected_client': selected_client,
        'integrations_by_channel': integrations_by_channel,
        'channel_choices': IntegrationAccount.CHANNEL_CHOICES,
        'available_google_ads_metrics': SelectedMetric.GOOGLE_ADS_METRICS,
        'available_ga4_metrics': SelectedMetric.GA4_METRICS,
        'available_meta_ads_metrics': SelectedMetric.META_ADS_METRICS,
        'active_nav': 'integrations',
    }
    
    return render(request, 'reportai/integrations.html', context)


def integration_account_detail(request, account_id):
    """
    Vista detallada de una cuenta de integración específica.
    Muestra campañas y métricas seleccionadas.
    """
    account = get_object_or_404(IntegrationAccount, id=account_id)
    
    # Obtener métricas disponibles para este canal
    available_metrics = SelectedMetric.get_available_metrics(account.channel)
    selected_metric_keys = list(
        account.selected_metrics.filter(is_active=True).values_list('metric_key', flat=True)
    )
    
    context = {
        'account': account,
        'selected_campaigns': account.selected_campaigns.filter(is_active=True),
        'selected_metrics': account.selected_metrics.filter(is_active=True),
        'available_metrics': available_metrics,
        'selected_metric_keys': selected_metric_keys,
    }
    
    return render(request, 'reportai/integrations/account_detail.html', context)


# ============================================================
# OAUTH FLOW - INICIO
# ============================================================

def oauth_start(request, channel):
    """
    Inicia el flujo OAuth2 para conectar una cuenta.
    
    Parámetros:
        channel: 'google_ads', 'ga4', o 'meta_ads'
        client_id: ID del cliente (query param)
    
    El flujo OAuth retorna todas las cuentas disponibles en ese login,
    y luego el usuario selecciona cuáles quiere agregar al cliente.
    """
    client_id = request.GET.get('client_id')
    
    if not client_id:
        messages.error(request, 'Debe seleccionar un cliente primero.')
        return redirect('reportai:integrations')
    
    # Verify client exists
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        messages.error(request, 'Cliente no encontrado.')
        return redirect('reportai:integrations')
    
    # Determine scope and auth URL based on channel
    if channel == 'google_ads':
        scope = GOOGLE_ADS_SCOPE
        auth_url = GOOGLE_AUTH_URL
        client_oauth_id = getattr(settings, 'GOOGLE_ADS_CLIENT_ID', '')
    elif channel == 'ga4':
        scope = GA4_SCOPE
        auth_url = GOOGLE_AUTH_URL
        client_oauth_id = getattr(settings, 'GOOGLE_ADS_CLIENT_ID', '')  # Same Google credentials
    elif channel == 'meta_ads':
        scope = META_ADS_SCOPE
        auth_url = META_AUTH_URL
        client_oauth_id = getattr(settings, 'META_APP_ID', '')
    else:
        messages.error(request, 'Tipo de integración no válido.')
        return redirect('reportai:integrations')
    
    # Generate state token to prevent CSRF and store integration info
    state_data = {
        'channel': channel,
        'client_id': str(client_id),
        'csrf_token': secrets.token_urlsafe(32)
    }
    state = json.dumps(state_data)
    
    # Store state in session for verification
    request.session['oauth_state'] = state
    
    # Build authorization URL
    redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '')
    
    if channel in ['google_ads', 'ga4']:
        params = {
            'client_id': client_oauth_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        }
    else:  # meta_ads
        params = {
            'client_id': client_oauth_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state,
        }
    
    full_auth_url = f"{auth_url}?{urlencode(params)}"
    return redirect(full_auth_url)


def oauth_callback(request):
    """
    Handle OAuth2 callback from Google/Meta.
    
    Después de autenticación exitosa:
    1. Intercambia el código por tokens
    2. Lista todas las cuentas disponibles en ese login
    3. Redirige a la página de selección de cuentas
    """
    error = request.GET.get('error')
    if error:
        messages.error(request, f'Error de autorización: {error}')
        return redirect('reportai:integrations')
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code or not state:
        messages.error(request, 'Respuesta de autorización incompleta.')
        return redirect('reportai:integrations')
    
    # Verify state to prevent CSRF
    stored_state = request.session.get('oauth_state')
    if state != stored_state:
        messages.error(request, 'Estado de autorización inválido.')
        return redirect('reportai:integrations')
    
    # Parse state data
    try:
        state_data = json.loads(state)
        channel = state_data['channel']
        client_id = state_data['client_id']
    except (json.JSONDecodeError, KeyError):
        messages.error(request, 'Estado de autorización corrupto.')
        return redirect('reportai:integrations')
    
    # Exchange code for tokens
    if channel in ['google_ads', 'ga4']:
        token_data = {
            'code': code,
            'client_id': getattr(settings, 'GOOGLE_ADS_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GOOGLE_ADS_CLIENT_SECRET', ''),
            'redirect_uri': getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', ''),
            'grant_type': 'authorization_code',
        }
        token_url = GOOGLE_TOKEN_URL
    else:  # meta_ads
        token_data = {
            'code': code,
            'client_id': getattr(settings, 'META_APP_ID', ''),
            'client_secret': getattr(settings, 'META_APP_SECRET', ''),
            'redirect_uri': getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', ''),
        }
        token_url = META_TOKEN_URL
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        tokens = response.json()
    except requests.RequestException as e:
        messages.error(request, f'Error al obtener tokens: {str(e)}')
        return redirect(f"/app/integrations/?client_id={client_id}")
    
    # Store tokens temporarily in session for account selection
    request.session['oauth_tokens'] = {
        'access_token': tokens.get('access_token'),
        'refresh_token': tokens.get('refresh_token'),
        'expires_in': tokens.get('expires_in', 3600),
        'channel': channel,
        'client_id': client_id,
    }
    
    # Clear OAuth state from session
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    
    # Redirect to account selection page
    return redirect(f"/app/integrations/select-accounts/?channel={channel}&client_id={client_id}")


def select_accounts_view(request):
    """
    Página para seleccionar qué cuentas agregar al cliente.
    
    Lista todas las cuentas disponibles en el login OAuth y permite
    al usuario seleccionar cuáles quiere agregar.
    """
    channel = request.GET.get('channel')
    client_id = request.GET.get('client_id')
    
    if not channel or not client_id:
        messages.error(request, 'Parámetros faltantes.')
        return redirect('reportai:integrations')
    
    # Get tokens from session
    oauth_tokens = request.session.get('oauth_tokens', {})
    
    if not oauth_tokens or oauth_tokens.get('channel') != channel:
        messages.error(request, 'Sesión OAuth expirada. Por favor, intenta de nuevo.')
        return redirect(f"/app/integrations/?client_id={client_id}")
    
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        messages.error(request, 'Cliente no encontrado.')
        return redirect('reportai:integrations')
    
    # Fetch available accounts from the API
    access_token = oauth_tokens.get('access_token')
    available_accounts = []
    api_error = None

    if channel == 'google_ads':
        refresh_token = oauth_tokens.get('refresh_token')
        if not refresh_token:
            api_error = 'OAuth no devolvió refresh_token. Reautoriza con prompt=consent.'
            available_accounts = []
        else:
            discovered_accounts, api_error = discover_customer_hierarchy(refresh_token)
            # Mostramos apenas contas operacionais para seleção de campanhas/relatórios.
            available_accounts = [a for a in discovered_accounts if not a.get('is_manager', False)]
    elif channel == 'ga4':
        available_accounts, api_error = fetch_ga4_properties(access_token)
    elif channel == 'meta_ads':
        available_accounts = fetch_meta_ad_accounts(access_token)

    if api_error:
        import logging
        logging.getLogger(__name__).error(f'[select_accounts_view] API error para {channel}: {api_error}')

    # Get already connected account IDs for this client and channel
    existing_account_ids = set(
        IntegrationAccount.objects.filter(
            client=client,
            channel=channel
        ).values_list('account_id', flat=True)
    )

    # Mark which accounts are already connected
    for account in available_accounts:
        account['already_connected'] = account['id'] in existing_account_ids

    context = {
        'client': client,
        'channel': channel,
        'channel_name': dict(IntegrationAccount.CHANNEL_CHOICES).get(channel, channel),
        'available_accounts': available_accounts,
        'has_accounts': len(available_accounts) > 0,
        'api_error': api_error,
    }
    
    return render(request, 'reportai/integrations/select_accounts.html', context)


def _auto_populate_metric_configs(client, channel):
    """
    Cria automaticamente um ClientMetricConfig para cada métrica disponível
    do canal recém-conectado. Usa get_or_create para ser idempotente —
    reconectar a mesma conta não duplica nem sobrescreve customizações existentes.
    """
    available = SelectedMetric.get_available_metrics(channel)
    for order, (metric_key, display_name) in enumerate(available):
        ClientMetricConfig.objects.get_or_create(
            client=client,
            platform=channel,
            metric_key=metric_key,
            defaults={
                'display_name': display_name,
                'is_visible': True,
                'order': order,
            },
        )


@require_POST
def save_selected_accounts(request):
    """
    Guarda las cuentas seleccionadas por el usuario.
    
    POST data:
        client_id: ID del cliente
        channel: Canal de la integración
        accounts: Lista de account IDs seleccionados
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        channel = data.get('channel')
        selected_accounts = data.get('accounts', [])  # Lista de contas selecionadas
        
        if not client_id or not channel:
            return JsonResponse({'error': 'Parámetros faltantes.'}, status=400)
        
        client = Client.objects.get(id=client_id)
        
        # Get tokens from session
        oauth_tokens = request.session.get('oauth_tokens', {})
        
        if not oauth_tokens:
            return JsonResponse({'error': 'Sesión OAuth expirada.'}, status=400)
        
        # Create integration accounts for each selected account
        created_count = 0
        for account_data in selected_accounts:
            customer_id = str(account_data.get('customer_id') or account_data.get('id') or '').replace('-', '')
            customer_name = account_data.get('customer_name') or account_data.get('name', '')
            login_customer_id = account_data.get('login_customer_id')
            if login_customer_id:
                login_customer_id = str(login_customer_id).replace('-', '')

            if not customer_id:
                continue

            # GA4 não tem etapa de campanhas: conectar direto.
            # Google Ads e Meta Ads ficam 'pending_selection' até o usuário escolher campanhas.
            account_status = 'connected' if channel == 'ga4' else 'pending_selection'

            _, created = IntegrationAccount.objects.update_or_create(
                client=client,
                channel=channel,
                account_id=customer_id,
                defaults={
                    'customer_id': customer_id,
                    'login_customer_id': login_customer_id,
                    'account_name': customer_name,
                    'customer_name': customer_name,
                    'status': account_status,
                    'access_token': oauth_tokens.get('access_token'),
                    'refresh_token': oauth_tokens.get('refresh_token'),
                    'token_expiry': timezone.now() + timedelta(seconds=oauth_tokens.get('expires_in', 3600)),
                    'extra_data': {
                        'login_customer_id': login_customer_id,
                    },
                }
            )
            if created:
                created_count += 1

            # Registra automaticamente todas as métricas do canal no ClientMetricConfig
            _auto_populate_metric_configs(client, channel)

        # Clear tokens from session
        if 'oauth_tokens' in request.session:
            del request.session['oauth_tokens']

        redirect_url = f'/app/integrations/?client_id={client_id}'

        return JsonResponse({
            'success': True,
            'message': f'Se agregaron {created_count} cuentas.',
            'redirect_url': redirect_url,
        })
        
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# CAMPAIGN SELECTION
# ============================================================

def select_campaigns_view(request, account_id):
    """
    Página para seleccionar campañas de una cuenta específica.
    """
    account = get_object_or_404(IntegrationAccount, id=account_id)
    
    # Fetch campaigns from the API
    available_campaigns = []
    api_error = None
    
    if account.channel == 'google_ads':
        available_campaigns, api_error = fetch_google_ads_campaigns(account)
    elif account.channel == 'meta_ads':
        available_campaigns = fetch_meta_campaigns(account)
    # GA4 no tiene "campañas" en el mismo sentido
    
    # Get already selected campaign IDs
    selected_campaign_ids = set(
        account.selected_campaigns.filter(is_active=True).values_list('campaign_id', flat=True)
    )
    
    # Mark which campaigns are already selected
    for campaign in available_campaigns:
        campaign['is_selected'] = campaign['id'] in selected_campaign_ids
    
    context = {
        'account': account,
        'client': account.client,
        'available_campaigns': available_campaigns,
        'has_campaigns': len(available_campaigns) > 0,
        'api_error': api_error,
    }
    
    return render(request, 'reportai/integrations/select_campaigns.html', context)


@require_POST
def save_selected_campaigns(request, account_id):
    """
    Guarda las campañas seleccionadas para una cuenta.
    """
    try:
        account = get_object_or_404(IntegrationAccount, id=account_id)
        data = json.loads(request.body)
        selected_campaigns = data.get('campaigns', [])  # Lista de {id, name, type}
        
        # Clear existing campaigns
        account.selected_campaigns.all().delete()
        
        # Create new campaign selections
        for campaign_data in selected_campaigns:
            SelectedCampaign.objects.create(
                integration=account,
                campaign_id=campaign_data.get('id'),
                campaign_name=campaign_data.get('name', ''),
                campaign_type=campaign_data.get('type', ''),
                is_active=True
            )

        # Marca a conta como conectada após o usuário configurar as campanhas
        if account.status == 'pending_selection':
            account.status = 'connected'
            account.save(update_fields=['status'])

        return JsonResponse({
            'success': True,
            'message': f'Se guardaron {len(selected_campaigns)} campañas.',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# METRICS SELECTION
# ============================================================

def select_metrics_view(request, account_id):
    """
    Página para seleccionar métricas de una cuenta específica.
    """
    account = get_object_or_404(IntegrationAccount, id=account_id)
    
    # Get available metrics for this channel
    available_metrics = SelectedMetric.get_available_metrics(account.channel)
    
    # Get already selected metric keys
    selected_metric_keys = set(
        account.selected_metrics.filter(is_active=True).values_list('metric_key', flat=True)
    )
    
    context = {
        'account': account,
        'client': account.client,
        'available_metrics': available_metrics,
        'selected_metric_keys': selected_metric_keys,
    }
    
    return render(request, 'reportai/integrations/select_metrics.html', context)


@require_POST
def save_selected_metrics(request, account_id):
    """
    Guarda las métricas seleccionadas para una cuenta.
    """
    try:
        account = get_object_or_404(IntegrationAccount, id=account_id)
        data = json.loads(request.body)
        selected_metrics = data.get('metrics', [])  # Lista de metric_keys
        
        # Get available metrics for this channel
        available_metrics = dict(SelectedMetric.get_available_metrics(account.channel))
        
        # Clear existing metrics
        account.selected_metrics.all().delete()
        
        # Create new metric selections
        for i, metric_key in enumerate(selected_metrics):
            if metric_key in available_metrics:
                SelectedMetric.objects.create(
                    integration=account,
                    metric_key=metric_key,
                    metric_name=available_metrics[metric_key],
                    is_active=True,
                    display_order=i
                )
        
        # Update account status to connected if it has campaigns (or is GA4)
        if account.status == 'pending_selection':
            account.status = 'connected'
            account.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Se guardaron {len(selected_metrics)} métricas.',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

def disconnect_account(request, account_id):
    """
    Desconecta y elimina una cuenta de integración.
    """
    account = get_object_or_404(IntegrationAccount, id=account_id)
    client_id = account.client.id
    account_name = account.display_name
    
    # Delete the account (cascades to campaigns and metrics)
    account.delete()
    
    messages.success(request, f'Cuenta "{account_name}" desconectada exitosamente.')
    return redirect(f"/app/integrations/?client_id={client_id}")


@require_POST
def update_account_name(request, account_id):
    """
    Actualiza el nombre amigable de una cuenta.
    """
    try:
        account = get_object_or_404(IntegrationAccount, id=account_id)
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({'error': 'El nombre no puede estar vacío.'}, status=400)
        
        account.account_name = new_name
        account.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Nombre actualizado.',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# API HELPERS - funções mock removidas; implementações reais em google_services.py
# fetch_google_ads_accounts, fetch_google_ads_campaigns, fetch_ga4_properties
# estão importadas no topo deste arquivo.
# ============================================================

def fetch_meta_ad_accounts(access_token):
    """
    Obtiene cuentas de Meta Ads.
    TODO: Implementar con Meta Marketing API cuando se configuren las credenciales.
    """
    return []


def fetch_meta_campaigns(account):
    """
    Obtiene campañas de Meta Ads.
    TODO: Implementar con Meta Marketing API cuando se configuren las credenciales.
    """
    return []


# ============================================================
# API ENDPOINTS - Status & Data
# ============================================================

def get_integration_status(request, client_id):
    """
    API endpoint para obtener el estado de todas las integraciones de un cliente.
    """
    try:
        client = Client.objects.get(id=client_id)
        
        integrations_by_channel = {}
        for channel, channel_name in IntegrationAccount.CHANNEL_CHOICES:
            accounts = IntegrationAccount.objects.filter(
                client=client,
                channel=channel
            )
            
            accounts_data = []
            for account in accounts:
                accounts_data.append({
                    'id': str(account.id),
                    'account_id': account.account_id,
                    'account_name': account.account_name,
                    'status': account.status,
                    'is_token_expired': account.is_token_expired(),
                    'last_sync': account.last_sync.isoformat() if account.last_sync else None,
                    'campaigns_count': account.selected_campaigns.filter(is_active=True).count(),
                    'metrics_count': account.selected_metrics.filter(is_active=True).count(),
                })
            
            if accounts_data:
                integrations_by_channel[channel] = {
                    'name': channel_name,
                    'accounts': accounts_data,
                    'total_accounts': len(accounts_data),
                    'connected_count': len([a for a in accounts_data if a['status'] == 'connected']),
                }
        
        return JsonResponse({
            'client_id': client_id,
            'client_name': client.name,
            'integrations': integrations_by_channel
        })
        
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado.'}, status=404)


def get_account_details(request, account_id):
    """
    API endpoint para obtener detalles de una cuenta específica.
    """
    try:
        account = IntegrationAccount.objects.get(id=account_id)
        
        return JsonResponse({
            'id': str(account.id),
            'client_id': account.client.id,
            'client_name': account.client.name,
            'channel': account.channel,
            'channel_name': account.get_channel_display(),
            'account_id': account.account_id,
            'account_name': account.account_name,
            'status': account.status,
            'is_token_expired': account.is_token_expired(),
            'last_sync': account.last_sync.isoformat() if account.last_sync else None,
            'campaigns': list(
                account.selected_campaigns.filter(is_active=True).values(
                    'campaign_id', 'campaign_name', 'campaign_type'
                )
            ),
            'metrics': list(
                account.selected_metrics.filter(is_active=True).values(
                    'metric_key', 'metric_name'
                )
            ),
        })
        
    except IntegrationAccount.DoesNotExist:
        return JsonResponse({'error': 'Cuenta no encontrada.'}, status=404)


def api_fetch_account_data(request, account_id):
    """
    API endpoint para buscar métricas reais de uma conta integrada.
    Parâmetros GET: date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
    """
    from datetime import date, timedelta as td
    try:
        account = get_object_or_404(IntegrationAccount, id=account_id)

        date_to_str = request.GET.get('date_to', str(date.today()))
        date_from_str = request.GET.get('date_from', str(date.today() - td(days=6)))

        metric_keys = list(
            account.selected_metrics.filter(is_active=True).values_list('metric_key', flat=True)
        )

        if account.channel == 'google_ads':
            result = fetch_google_ads_metrics(account, date_from_str, date_to_str, metric_keys)
        elif account.channel == 'ga4':
            result = fetch_ga4_metrics(account, date_from_str, date_to_str, metric_keys)
        else:
            return JsonResponse({'error': 'Canal no soportado aún.'}, status=400)

        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=502)

        # Atualiza timestamp de sincronização
        account.last_sync = timezone.now()
        account.save(update_fields=['last_sync'])

        return JsonResponse({'success': True, 'data': result})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# LEGACY SUPPORT - Mantener compatibilidad temporal
# ============================================================

# Alias para compatibilidad con URLs antiguas
def oauth_disconnect(request, integration_type, client_id):
    """
    [DEPRECATED] Usar disconnect_account en su lugar.
    Mantenido para compatibilidad con URLs antiguas.
    """
    messages.warning(request, 'Esta función está obsoleta. Por favor, usa el nuevo flujo de integraciones.')
    return redirect(f"/app/integrations/?client_id={client_id}")


@require_POST
def save_metrics(request):
    """
    [DEPRECATED] Usar save_selected_metrics en su lugar.
    Mantenido para compatibilidad con código antiguo.
    """
    return JsonResponse({'error': 'Esta función está obsoleta. Usa el nuevo endpoint.'}, status=410)


# ============================================================
# API — TIMELINE
# ============================================================

@login_required
@require_POST
def api_timeline_create(request, client_id):
    """Cria uma nova entrada na timeline do cliente."""
    client = get_object_or_404(Client, id=client_id, owner=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'El título es obligatorio.'}, status=400)

    date_val = data.get('date', '').strip()
    if not date_val:
        return JsonResponse({'error': 'La fecha es obligatoria.'}, status=400)

    entry = TimelineEntry.objects.create(
        client=client,
        date=date_val,
        badge_type=data.get('badge_type', 'actualizacion'),
        badge_color=data.get('badge_color', 'blue'),
        title=title,
        description=data.get('description', ''),
    )
    return JsonResponse({
        'success': True,
        'id': entry.id,
        'date': str(entry.date),
        'badge_type': entry.badge_type,
        'badge_color': entry.badge_color,
        'title': entry.title,
        'description': entry.description,
    })


@login_required
@require_POST
def api_timeline_delete(request, entry_id):
    """Deleta uma entrada da timeline do cliente."""
    entry = get_object_or_404(TimelineEntry, id=entry_id, client__owner=request.user)
    entry.delete()
    return JsonResponse({'success': True})


# ============================================================
# DASHBOARD PÚBLICO DO CLIENTE
# ============================================================

def _format_metric_value(metric_key, value):
    """Formata o valor de uma métrica para exibição no dashboard público."""
    if value is None:
        return '—'
    if metric_key in ('cpc', 'spend', 'cpm'):
        return f'€{value:.2f}'
    if metric_key in ('bounce_rate', 'ctr'):
        return f'{value}%'
    if isinstance(value, float):
        return f'{value:.1f}'
    return str(int(value))


def _build_dashboard_context(client, log) -> dict:
    """
    Monta o contexto completo para o template public_dashboard.html.
    Aceita tanto um ReportLog real quanto um SimpleNamespace (para preview sem salvar).
    """
    # Métricas em destaque — lidas do snapshot do relatório
    highlight_metrics = []

    current_week = {}
    previous_week = {}
    if log and log.metrics_snapshot:
        current_week = log.metrics_snapshot.get('current_week', {})
        previous_week = log.metrics_snapshot.get('previous_week', {})

    # Lê as chaves destacadas salvas no snapshot
    highlighted_keys = []
    if log and log.metrics_snapshot:
        highlighted_keys = log.metrics_snapshot.get('highlighted', [])

    # Mapeia (platform, metric_key) → config para evitar colisão quando dois platforms
    # partilham o mesmo metric_key (ex: 'conversions' em google_ads e meta_ads)
    configs_by_key = {
        (c.platform, c.metric_key): c
        for c in ClientMetricConfig.objects.filter(client=client)
    }

    for item in highlighted_keys:
        # Suporta tanto objetos {key, platform} (formato novo) como strings planas (legado)
        if isinstance(item, dict):
            key = item.get('key', '')
            platform = item.get('platform', '')
        else:
            key = str(item)
            platform = None

        # Lookup preciso por (platform, key); fallback por key apenas para snapshots antigos
        config = configs_by_key.get((platform, key)) if platform else None
        if not config:
            for (p_iter, k_iter), c_iter in configs_by_key.items():
                if k_iter == key:
                    config = c_iter
                    break
        if not config:
            continue

        p = config.platform
        current_val = current_week.get(p, {}).get(key)
        # Fallback: procura em todas as plataformas do snapshot (seguro — chaves são únicas)
        if current_val is None:
            for plat_data in current_week.values():
                if isinstance(plat_data, dict) and key in plat_data:
                    current_val = plat_data[key]
                    break
        if current_val is None:
            current_val = 0.0

        prev_val = previous_week.get(p, {}).get(key)
        if prev_val is None:
            for plat_data in previous_week.values():
                if isinstance(plat_data, dict) and key in plat_data:
                    prev_val = plat_data[key]
                    break
        delta = None
        if prev_val and prev_val != 0:
            delta = round((current_val - prev_val) / abs(prev_val) * 100, 1)

        highlight_metrics.append({
            'display_name': config.display_name,
            'metric_key': key,
            'platform': p,
            'value': current_val,
            'formatted_value': _format_metric_value(key, current_val),
            'delta': delta,
            'delta_abs': round(abs(delta), 1) if delta is not None else None,
            'delta_class': ('up' if delta > 0 else ('down' if delta < 0 else 'flat')) if delta is not None else '',
            'delta_arrow': ('▲' if delta > 0 else ('▼' if delta < 0 else '—')) if delta is not None else '',
        })

    # Timeline manual de ações do cliente
    timeline_entries = (
        TimelineEntry.objects
        .filter(client=client)
        .order_by('-date')
    )

    return {
        'client': client,
        'latest_log': log,
        'highlight_metrics': highlight_metrics,
        'timeline_entries': timeline_entries,
    }


def public_dashboard_view(request, token):
    """
    Dashboard público acessível sem login via token único do cliente.
    Exibe métricas em destaque, insight da IA, score e timeline de ações.
    """
    client = get_object_or_404(Client, dashboard_token=token)

    latest_log = (
        ReportLog.objects
        .filter(client=client)
        .order_by('-sent_at')
        .first()
    )

    context = _build_dashboard_context(client, latest_log)
    return render(request, 'reportai/public_dashboard.html', context)


def public_dashboard_by_slug(request, slug):
    """Rota amigável /dashboard/<slug>/; com fallback para UUID (links antigos)."""
    try:
        client = Client.objects.get(dashboard_slug=slug)
    except Client.DoesNotExist:
        # Fallback: tenta interpretar como UUID para links já enviados
        try:
            token = uuid_module.UUID(str(slug))
            client = get_object_or_404(Client, dashboard_token=token)
        except (ValueError, AttributeError):
            raise Http404
    return public_dashboard_view(request, token=client.dashboard_token)


@require_POST
@login_required
def api_report_preview_dashboard(request):
    """
    Renderiza o template public_dashboard.html com dados provisórios (sem salvar no banco).
    Permite que a agência visualize como o dashboard do cliente ficará antes de enviar.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    client_id = data.get('client_id')
    if not client_id:
        return JsonResponse({'success': False, 'error': 'client_id obrigatório.'}, status=400)

    client = get_object_or_404(Client, id=client_id, owner=request.user)

    # Monta snapshot com highlighted e dashboard_insight do payload
    metrics_snapshot = data.get('metrics_snapshot', {})
    if not isinstance(metrics_snapshot, dict):
        metrics_snapshot = {}
    metrics_snapshot['highlighted'] = data.get('highlighted_metrics', [])

    # Cria um log falso com a interface que o template espera (não persiste no banco)
    fake_log = SimpleNamespace(
        client=client,
        metrics_snapshot=metrics_snapshot,
        campaign_score=data.get('campaign_score') or 0,
        score_reason=str(data.get('score_reason', '')),
        message_generated=str(data.get('message_generated', '')),
        dashboard_insight=str(data.get('dashboard_insight', '')),
        sent_at=timezone.now(),
    )

    context = _build_dashboard_context(client, fake_log)
    html = render_to_string('reportai/public_dashboard.html', context, request=request)
    return JsonResponse({'html': html})
