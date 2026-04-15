import json
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

import requests

from .models import Client, ClientIntegration, SelectedMetric


# Google OAuth2 endpoints
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'

# OAuth scopes
GOOGLE_ADS_SCOPE = 'https://www.googleapis.com/auth/adwords'
GA4_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'


# Auth Views
def login_view(request):
    """Login page."""
    return render(request, 'reportai/auth/login.html')


def register_view(request):
    """Registration page."""
    return render(request, 'reportai/auth/register.html')


def onboarding_view(request):
    """Onboarding flow after registration."""
    return render(request, 'reportai/auth/onboarding.html')


def logout_view(request):
    """Logout and redirect to login."""
    return redirect('reportai:login')


# Dashboard View
def dashboard_view(request):
    """Main dashboard page."""
    return render(request, 'reportai/dashboard.html')


# Clients Views
def clients_list_view(request):
    """List of all clients."""
    return render(request, 'reportai/clients/list.html')


def client_profile_view(request, client_id):
    """Individual client profile and report history."""
    context = {
        'client_id': client_id,
    }
    return render(request, 'reportai/clients/profile.html', context)


# Reports Views
def reports_list_view(request):
    """Reports history list."""
    return render(request, 'reportai/reports/list.html')


def report_generate_view(request):
    """Generate new report with AI."""
    return render(request, 'reportai/reports/generate.html')


# Integrations View
def integrations_view(request):
    """Integrations management page with client selection."""
    # Get all clients for the dropdown (in production, filter by logged-in user)
    clients = Client.objects.all()
    
    # Get selected client from query param
    selected_client_id = request.GET.get('client_id')
    selected_client = None
    google_ads_integration = None
    ga4_integration = None
    google_ads_metrics = []
    ga4_metrics = []
    
    if selected_client_id:
        try:
            selected_client = Client.objects.get(id=selected_client_id)
            
            # Get integrations for this client
            google_ads_integration = ClientIntegration.objects.filter(
                client=selected_client,
                integration_type='google_ads'
            ).first()
            
            ga4_integration = ClientIntegration.objects.filter(
                client=selected_client,
                integration_type='ga4'
            ).first()
            
            # Get selected metrics
            if google_ads_integration:
                google_ads_metrics = list(
                    google_ads_integration.selected_metrics.filter(is_active=True)
                    .values_list('metric_key', flat=True)
                )
            
            if ga4_integration:
                ga4_metrics = list(
                    ga4_integration.selected_metrics.filter(is_active=True)
                    .values_list('metric_key', flat=True)
                )
        except Client.DoesNotExist:
            pass
    
    context = {
        'clients': clients,
        'selected_client': selected_client,
        'google_ads_integration': google_ads_integration,
        'ga4_integration': ga4_integration,
        'google_ads_metrics': google_ads_metrics,
        'ga4_metrics': ga4_metrics,
        'available_google_ads_metrics': SelectedMetric.GOOGLE_ADS_METRICS,
        'available_ga4_metrics': SelectedMetric.GA4_METRICS,
    }
    
    return render(request, 'reportai/integrations.html', context)


# OAuth Views
def oauth_start(request, integration_type):
    """
    Start OAuth2 flow for Google Ads or GA4.
    integration_type: 'google_ads' or 'ga4'
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
    
    # Determine scope based on integration type
    if integration_type == 'google_ads':
        scope = GOOGLE_ADS_SCOPE
    elif integration_type == 'ga4':
        scope = GA4_SCOPE
    else:
        messages.error(request, 'Tipo de integración no válido.')
        return redirect('reportai:integrations')
    
    # Generate state token to prevent CSRF and store integration info
    state_data = {
        'integration_type': integration_type,
        'client_id': client_id,
        'csrf_token': secrets.token_urlsafe(32)
    }
    state = json.dumps(state_data)
    
    # Store state in session for verification
    request.session['oauth_state'] = state
    
    # Build authorization URL
    params = {
        'client_id': settings.GOOGLE_ADS_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': scope,
        'access_type': 'offline',  # Request refresh token
        'prompt': 'consent',  # Force consent screen to get refresh token
        'state': state,
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)


def oauth_callback(request):
    """
    Handle OAuth2 callback from Google.
    Exchange authorization code for tokens and save to database.
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
        integration_type = state_data['integration_type']
        client_id = state_data['client_id']
    except (json.JSONDecodeError, KeyError):
        messages.error(request, 'Estado de autorización corrupto.')
        return redirect('reportai:integrations')
    
    # Exchange code for tokens
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_ADS_CLIENT_ID,
        'client_secret': settings.GOOGLE_ADS_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    
    try:
        response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        response.raise_for_status()
        tokens = response.json()
    except requests.RequestException as e:
        messages.error(request, f'Error al obtener tokens: {str(e)}')
        return redirect('reportai:integrations')
    
    # Get or create integration
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        messages.error(request, 'Cliente no encontrado.')
        return redirect('reportai:integrations')
    
    integration, created = ClientIntegration.objects.get_or_create(
        client=client,
        integration_type=integration_type,
        defaults={'status': 'connected'}
    )
    
    # Update tokens
    integration.access_token = tokens.get('access_token')
    integration.refresh_token = tokens.get('refresh_token', integration.refresh_token)
    
    # Calculate token expiry
    expires_in = tokens.get('expires_in', 3600)
    integration.token_expiry = timezone.now() + timedelta(seconds=expires_in)
    integration.status = 'connected'
    integration.last_sync = timezone.now()
    integration.save()
    
    # Clear OAuth state from session
    del request.session['oauth_state']
    
    # Redirect to metric selection
    integration_name = 'Google Ads' if integration_type == 'google_ads' else 'GA4'
    messages.success(request, f'¡{integration_name} conectado exitosamente! Ahora selecciona las métricas.')
    
    return redirect(f"{request.build_absolute_uri('/app/integrations/')}?client_id={client_id}&select_metrics={integration_type}")


def oauth_disconnect(request, integration_type, client_id):
    """Disconnect an integration for a client."""
    try:
        client = Client.objects.get(id=client_id)
        integration = ClientIntegration.objects.get(
            client=client,
            integration_type=integration_type
        )
        
        # Clear tokens and update status
        integration.access_token = None
        integration.refresh_token = None
        integration.token_expiry = None
        integration.status = 'disconnected'
        integration.save()
        
        # Also clear selected metrics
        integration.selected_metrics.all().delete()
        
        integration_name = 'Google Ads' if integration_type == 'google_ads' else 'GA4'
        messages.success(request, f'{integration_name} desconectado exitosamente.')
        
    except (Client.DoesNotExist, ClientIntegration.DoesNotExist):
        messages.error(request, 'Integración no encontrada.')
    
    return redirect(f"/app/integrations/?client_id={client_id}")


@require_POST
def save_metrics(request):
    """Save selected metrics for an integration."""
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        integration_type = data.get('integration_type')
        metrics = data.get('metrics', [])
        
        if not client_id or not integration_type:
            return JsonResponse({'error': 'Faltan parámetros requeridos.'}, status=400)
        
        # Get integration
        try:
            client = Client.objects.get(id=client_id)
            integration = ClientIntegration.objects.get(
                client=client,
                integration_type=integration_type
            )
        except (Client.DoesNotExist, ClientIntegration.DoesNotExist):
            return JsonResponse({'error': 'Integración no encontrada.'}, status=404)
        
        # Get available metrics for this integration type
        available_metrics = dict(SelectedMetric.get_available_metrics(integration_type))
        
        # Clear existing metrics
        integration.selected_metrics.all().delete()
        
        # Save new metrics
        for metric_key in metrics:
            if metric_key in available_metrics:
                SelectedMetric.objects.create(
                    integration=integration,
                    metric_key=metric_key,
                    metric_name=available_metrics[metric_key],
                    is_active=True
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Se guardaron {len(metrics)} métricas.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_integration_status(request, client_id):
    """API endpoint to get integration status for a client."""
    try:
        client = Client.objects.get(id=client_id)
        
        integrations = {}
        for integration in client.integrations.all():
            integrations[integration.integration_type] = {
                'status': integration.status,
                'last_sync': integration.last_sync.isoformat() if integration.last_sync else None,
                'is_token_expired': integration.is_token_expired(),
                'selected_metrics': list(
                    integration.selected_metrics.filter(is_active=True)
                    .values('metric_key', 'metric_name')
                )
            }
        
        return JsonResponse({
            'client_id': client_id,
            'client_name': client.name,
            'integrations': integrations
        })
        
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado.'}, status=404)
