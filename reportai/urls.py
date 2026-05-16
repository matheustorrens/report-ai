from django.urls import path
from . import views

app_name = 'reportai'

urlpatterns = [
    # ============================================================
    # AUTH
    # ============================================================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.agency_profile_view, name='agency_profile'),
    
    # ============================================================
    # DASHBOARD
    # ============================================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ============================================================
    # CLIENTS
    # ============================================================
    path('clients/', views.clients_list_view, name='clients'),
    path('clients/create/', views.client_create_view, name='client_create'),
    path('clients/<int:client_id>/', views.client_profile_view, name='client_profile'),
    path('clients/<int:client_id>/edit/', views.client_edit_view, name='client_edit'),
    path('clients/<int:client_id>/delete/', views.client_delete_view, name='client_delete'),
    path('clients/<int:client_id>/metrics/', views.client_metrics_config_view, name='client_metrics_config'),
    path('api/clients/', views.api_create_client, name='api_create_client'),
    path('api/clients/<int:client_id>/', views.api_update_client, name='api_update_client'),
    path('api/clients/<int:client_id>/delete/', views.api_delete_client, name='api_delete_client'),
    path('api/clients/<int:client_id>/metrics/', views.api_client_metrics, name='api_client_metrics'),
    path('api/legal/accept-dpa/', views.api_accept_dpa, name='api_accept_dpa'),
    
    # ============================================================
    # REPORTS
    # ============================================================
    path('reports/', views.reports_list_view, name='reports'),
    path('reports/generate/', views.report_generate_view, name='report_generate'),
    path('api/reports/preview/', views.api_report_preview, name='api_report_preview'),
    path('api/reports/preview-dashboard/', views.api_report_preview_dashboard, name='api_report_preview_dashboard'),
    path('api/reports/send/', views.api_report_send, name='api_report_send'),
    path('api/clients/<int:client_id>/report-config/', views.api_client_report_config, name='api_client_report_config'),
    
    # ============================================================
    # INTEGRATIONS - Main Views
    # ============================================================
    path('integrations/', views.integrations_view, name='integrations'),
    path('integrations/account/<uuid:account_id>/', views.integration_account_detail, name='account_detail'),
    
    # ============================================================
    # INTEGRATIONS - OAuth Flow
    # ============================================================
    # Start OAuth flow for a channel (google_ads, ga4, meta_ads)
    path('oauth/start/<str:channel>/', views.oauth_start, name='oauth_start'),
    # OAuth callback (handles all channels)
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    
    # ============================================================
    # INTEGRATIONS - Account Selection (after OAuth)
    # ============================================================
    path('integrations/select-accounts/', views.select_accounts_view, name='select_accounts'),
    path('api/integrations/save-accounts/', views.save_selected_accounts, name='save_accounts'),
    
    # ============================================================
    # INTEGRATIONS - Campaign Selection
    # ============================================================
    path('integrations/account/<uuid:account_id>/campaigns/', views.select_campaigns_view, name='select_campaigns'),
    path('api/integrations/account/<uuid:account_id>/campaigns/', views.save_selected_campaigns, name='save_campaigns'),
    
    # ============================================================
    # INTEGRATIONS - Metrics Selection
    # ============================================================
    path('integrations/account/<uuid:account_id>/metrics/', views.select_metrics_view, name='select_metrics'),
    path('api/integrations/account/<uuid:account_id>/metrics/', views.save_selected_metrics, name='save_metrics'),
    
    # ============================================================
    # INTEGRATIONS - Account Management
    # ============================================================
    path('integrations/account/<uuid:account_id>/disconnect/', views.disconnect_account, name='disconnect_account'),
    path('api/integrations/account/<uuid:account_id>/name/', views.update_account_name, name='update_account_name'),
    
    # ============================================================
    # API - Status & Data
    # ============================================================
    path('api/integrations/<int:client_id>/', views.get_integration_status, name='integration_status'),
    path('api/integrations/account/<uuid:account_id>/', views.get_account_details, name='account_details'),
    path('api/integrations/account/<uuid:account_id>/data/', views.api_fetch_account_data, name='account_data'),
    
    # ============================================================
    # LEGACY SUPPORT (Deprecated - mantidos para compatibilidad)
    # ============================================================
    path('oauth/disconnect/<str:integration_type>/<int:client_id>/', views.oauth_disconnect, name='oauth_disconnect'),
    path('api/metrics/save/', views.save_metrics, name='save_metrics_legacy'),

    # ============================================================
    # API - DASHBOARD
    # ============================================================
    path('api/clients/<int:client_id>/timeline/', views.api_timeline_create, name='api_timeline_create'),
    path('api/timeline/<int:entry_id>/delete/', views.api_timeline_delete, name='api_timeline_delete'),
]
