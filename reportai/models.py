from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Client(models.Model):
    """
    Represents a client of the marketing agency.
    Each client can have multiple integrations (Google Ads, GA4, etc.)
    """
    name = models.CharField(max_length=255, verbose_name="Nombre del cliente")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name="Empresa")
    
    # Agency user who owns this client
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='clients',
        verbose_name="Propietario"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ClientIntegration(models.Model):
    """
    Stores OAuth tokens for each client integration.
    Each client can have multiple integrations (Google Ads, GA4, etc.)
    """
    INTEGRATION_TYPES = [
        ('google_ads', 'Google Ads'),
        ('ga4', 'Google Analytics 4'),
    ]
    
    STATUS_CHOICES = [
        ('connected', 'Conectado'),
        ('disconnected', 'Desconectado'),
        ('action_required', 'Acción Necesaria'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='integrations',
        verbose_name="Cliente"
    )
    integration_type = models.CharField(
        max_length=50,
        choices=INTEGRATION_TYPES,
        verbose_name="Tipo de integración"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='disconnected',
        verbose_name="Estado"
    )
    
    # OAuth tokens
    access_token = models.TextField(blank=True, null=True, verbose_name="Access Token")
    refresh_token = models.TextField(blank=True, null=True, verbose_name="Refresh Token")
    token_expiry = models.DateTimeField(blank=True, null=True, verbose_name="Expiración del token")
    
    # Google Ads specific - Customer ID of the client's account
    google_ads_customer_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name="Google Ads Customer ID"
    )
    
    # GA4 specific - Property ID
    ga4_property_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="GA4 Property ID"
    )
    
    last_sync = models.DateTimeField(blank=True, null=True, verbose_name="Última sincronización")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Integración de Cliente"
        verbose_name_plural = "Integraciones de Clientes"
        unique_together = ['client', 'integration_type']
    
    def __str__(self):
        return f"{self.client.name} - {self.get_integration_type_display()}"
    
    def is_token_expired(self):
        """Check if the access token has expired."""
        if not self.token_expiry:
            return True
        return timezone.now() >= self.token_expiry


class SelectedMetric(models.Model):
    """
    Stores which metrics the agency selected for each client integration.
    These metrics will be pulled when generating reports.
    """
    # Google Ads available metrics
    GOOGLE_ADS_METRICS = [
        ('impressions', 'Impresiones'),
        ('clicks', 'Clics'),
        ('cost', 'Coste'),
        ('conversions', 'Conversiones'),
        ('conversion_value', 'Valor de conversión'),
        ('ctr', 'CTR (Click-through rate)'),
        ('cpc', 'CPC (Coste por clic)'),
        ('cpa', 'CPA (Coste por adquisición)'),
        ('roas', 'ROAS (Return on ad spend)'),
        ('conversion_rate', 'Tasa de conversión'),
    ]
    
    # GA4 available metrics
    GA4_METRICS = [
        ('sessions', 'Sesiones'),
        ('users', 'Usuarios'),
        ('new_users', 'Usuarios nuevos'),
        ('pageviews', 'Páginas vistas'),
        ('bounce_rate', 'Tasa de rebote'),
        ('session_duration', 'Duración de sesión'),
        ('pages_per_session', 'Páginas por sesión'),
        ('engaged_sessions', 'Sesiones con interacción'),
        ('engagement_rate', 'Tasa de interacción'),
        ('events', 'Eventos'),
    ]
    
    integration = models.ForeignKey(
        ClientIntegration,
        on_delete=models.CASCADE,
        related_name='selected_metrics',
        verbose_name="Integración"
    )
    metric_key = models.CharField(max_length=100, verbose_name="Clave de la métrica")
    metric_name = models.CharField(max_length=255, verbose_name="Nombre de la métrica")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Métrica Seleccionada"
        verbose_name_plural = "Métricas Seleccionadas"
        unique_together = ['integration', 'metric_key']
    
    def __str__(self):
        return f"{self.integration} - {self.metric_name}"
    
    @classmethod
    def get_available_metrics(cls, integration_type):
        """Return available metrics based on integration type."""
        if integration_type == 'google_ads':
            return cls.GOOGLE_ADS_METRICS
        elif integration_type == 'ga4':
            return cls.GA4_METRICS
        return []
