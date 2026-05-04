"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include

from reportai.views import oauth_callback, public_dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
    path('app/', include('reportai.urls', namespace='reportai')),
    
    # OAuth callback at root level (configured in Google Cloud)
    path('oauth/callback', oauth_callback, name='oauth_callback'),

    # Dashboard público do cliente (sem login)
    path('dashboard/<uuid:token>/', public_dashboard_view, name='public_dashboard'),
]
