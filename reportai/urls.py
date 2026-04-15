from django.urls import path
from . import views

app_name = 'reportai'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Clients
    path('clients/', views.clients_list_view, name='clients'),
    path('clients/<int:client_id>/', views.client_profile_view, name='client_profile'),
    
    # Reports
    path('reports/', views.reports_list_view, name='reports'),
    path('reports/generate/', views.report_generate_view, name='report_generate'),
    
    # Integrations
    path('integrations/', views.integrations_view, name='integrations'),
    
    # OAuth - Start flow
    path('oauth/start/<str:integration_type>/', views.oauth_start, name='oauth_start'),
    path('oauth/disconnect/<str:integration_type>/<int:client_id>/', views.oauth_disconnect, name='oauth_disconnect'),
    
    # API - Metrics
    path('api/metrics/save/', views.save_metrics, name='save_metrics'),
    path('api/integrations/<int:client_id>/', views.get_integration_status, name='integration_status'),
]
