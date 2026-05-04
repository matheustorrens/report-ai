from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid


class Client(models.Model):
    """
    Representa un cliente de la agencia de marketing.
    Cada cliente puede tener múltiples cuentas de integración (Google Ads, GA4, Meta Ads, etc.)
    
    Jerarquía: Agencia (User) → Cliente → N Cuentas por canal → N Campañas por cuenta
    """
    KNOWLEDGE_LEVEL_CHOICES = [
        ('leigo', 'Leigo (lenguaje de negocio)'),
        ('avancado', 'Avanzado (términos técnicos)'),
    ]

    SEND_CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Email + WhatsApp'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nombre del cliente")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name="Empresa")

    # Configuração de relatórios
    knowledge_level = models.CharField(
        max_length=10,
        choices=KNOWLEDGE_LEVEL_CHOICES,
        default='leigo',
        verbose_name="Nivel de conocimiento",
        help_text="Define el tono del mensaje generado por la IA"
    )
    send_channel = models.CharField(
        max_length=10,
        choices=SEND_CHANNEL_CHOICES,
        default='email',
        verbose_name="Canal de envío"
    )
    report_frequency_days = models.IntegerField(
        default=7,
        verbose_name="Frecuencia (días)",
        help_text="7 = semanal, 14 = quincenal, 30 = mensual"
    )
    next_report_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Próximo envío"
    )

    # Token público único para o dashboard do cliente (nunca muda)
    dashboard_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Token del dashboard público"
    )

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
    
    def get_integrations_by_channel(self, channel):
        """Retorna todas las cuentas de integración de un canal específico."""
        return self.integrations.filter(channel=channel, status='connected')
    
    def get_all_active_integrations(self):
        """Retorna todas las integraciones activas agrupadas por canal."""
        integrations = {}
        for channel, _ in IntegrationAccount.CHANNEL_CHOICES:
            channel_integrations = self.integrations.filter(channel=channel, status='connected')
            if channel_integrations.exists():
                integrations[channel] = channel_integrations
        return integrations


class IntegrationAccount(models.Model):
    """
    Representa una CUENTA de integración para un canal específico.
    
    IMPORTANTE: Un cliente puede tener MÚLTIPLES cuentas del mismo canal.
    Ejemplo: 
        - Cliente "Marca X" puede tener:
            - Cuenta Google Ads "123-456-7890" (Search)
            - Cuenta Google Ads "987-654-3210" (Shopping)
            - Cuenta GA4 "123456789" (Sitio Principal)
            - Cuenta Meta Ads "act_123456" (Facebook/Instagram)
    
    Cada cuenta de integración almacena:
    - Tokens OAuth para esa cuenta específica
    - ID y nombre de la cuenta externa
    - Campañas seleccionadas
    - Métricas seleccionadas
    """
    CHANNEL_CHOICES = [
        ('google_ads', 'Google Ads'),
        ('ga4', 'Google Analytics 4'),
        ('meta_ads', 'Meta Ads (Facebook/Instagram)'),
    ]
    
    STATUS_CHOICES = [
        ('connected', 'Conectado'),
        ('disconnected', 'Desconectado'),
        ('pending_selection', 'Pendiente de Selección'),
        ('token_expired', 'Token Expirado'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='integrations',
        verbose_name="Cliente"
    )
    
    channel = models.CharField(
        max_length=50,
        choices=CHANNEL_CHOICES,
        verbose_name="Canal"
    )
    
    # Identificación de la cuenta externa
    account_id = models.CharField(
        max_length=100,
        verbose_name="ID de la Cuenta",
        help_text="ID externo de la cuenta (ej: '123-456-7890' para Google Ads)"
    )
    customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Customer ID",
        help_text="ID operacional da conta Google Ads (sem hífens)"
    )
    login_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Login Customer ID",
        help_text="ID da conta MCC usada no header login-customer-id"
    )
    account_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre de la Cuenta",
        help_text="Nombre amigable para mostrar en la UI (ej: 'Marca X - Search')"
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Customer Name",
        help_text="Nome descritivo da conta Google Ads"
    )
    
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='disconnected',
        verbose_name="Estado"
    )
    
    # OAuth tokens - específicos para esta cuenta
    access_token = models.TextField(blank=True, null=True, verbose_name="Access Token")
    refresh_token = models.TextField(blank=True, null=True, verbose_name="Refresh Token")
    token_expiry = models.DateTimeField(blank=True, null=True, verbose_name="Expiración del token")
    
    # Campos adicionales específicos del canal (para datos que necesitamos guardar)
    # Ejemplo: manager_account_id para Google Ads MCC
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos Adicionales",
        help_text="Datos específicos del canal en formato JSON"
    )
    
    last_sync = models.DateTimeField(blank=True, null=True, verbose_name="Última sincronización")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cuenta de Integración"
        verbose_name_plural = "Cuentas de Integración"
        # Un cliente puede tener múltiples cuentas del mismo canal,
        # pero no puede tener la misma cuenta_id duplicada para el mismo canal
        unique_together = ['client', 'channel', 'account_id']
        ordering = ['client', 'channel', 'account_name']
    
    def __str__(self):
        name = self.account_name or self.account_id
        return f"{self.client.name} - {self.get_channel_display()} - {name}"
    
    def is_token_expired(self):
        """Verifica si el access token ha expirado."""
        if not self.token_expiry:
            return True
        return timezone.now() >= self.token_expiry
    
    def get_active_campaigns(self):
        """Retorna las campañas activas seleccionadas para esta cuenta."""
        return self.selected_campaigns.filter(is_active=True)
    
    def get_active_metrics(self):
        """Retorna las métricas activas seleccionadas para esta cuenta."""
        return self.selected_metrics.filter(is_active=True)
    
    @property
    def display_name(self):
        """Nombre para mostrar en la UI."""
        return self.account_name or f"{self.get_channel_display()} ({self.account_id})"


class SelectedCampaign(models.Model):
    """
    Representa una campaña seleccionada para incluir en los reportes.
    
    Cada cuenta de integración puede tener múltiples campañas seleccionadas.
    Ejemplo:
        - IntegrationAccount "Google Ads - Search"
            - Campaña "Brand Keywords"
            - Campaña "Generic Keywords"
            - Campaña "Remarketing"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    integration = models.ForeignKey(
        IntegrationAccount,
        on_delete=models.CASCADE,
        related_name='selected_campaigns',
        verbose_name="Cuenta de Integración"
    )
    
    campaign_id = models.CharField(
        max_length=100,
        verbose_name="ID de la Campaña",
        help_text="ID externo de la campaña"
    )
    campaign_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre de la Campaña"
    )
    
    # Tipo de campaña (útil para filtros y visualización)
    campaign_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Tipo de Campaña",
        help_text="Ej: 'SEARCH', 'DISPLAY', 'SHOPPING', 'VIDEO'"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Si está activa, se incluirá en los reportes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Campaña Seleccionada"
        verbose_name_plural = "Campañas Seleccionadas"
        unique_together = ['integration', 'campaign_id']
        ordering = ['campaign_name']
    
    def __str__(self):
        return f"{self.integration.display_name} - {self.campaign_name or self.campaign_id}"


class SelectedMetric(models.Model):
    """
    Almacena las métricas seleccionadas por la agencia para cada cuenta de integración.
    Estas métricas se utilizarán al generar los reportes.
    """
    # Métricas disponibles por canal
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
        ('avg_position', 'Posición promedio'),
        ('search_impression_share', 'Cuota de impresiones'),
    ]
    
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
        ('conversions', 'Conversiones'),
        ('revenue', 'Ingresos'),
    ]
    
    META_ADS_METRICS = [
        ('impressions', 'Impresiones'),
        ('reach', 'Alcance'),
        ('clicks', 'Clics'),
        ('spend', 'Gasto'),
        ('cpm', 'CPM'),
        ('cpc', 'CPC'),
        ('ctr', 'CTR'),
        ('frequency', 'Frecuencia'),
        ('conversions', 'Conversiones'),
        ('conversion_value', 'Valor de conversión'),
        ('roas', 'ROAS'),
        ('video_views', 'Reproducciones de video'),
        ('video_thruplay', 'ThruPlay (videos completos)'),
    ]
    
    # Keeping auto-increment id for backwards compatibility
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Nullable temporariamente para permitir migração de dados existentes
    integration = models.ForeignKey(
        IntegrationAccount,
        on_delete=models.CASCADE,
        related_name='selected_metrics',
        verbose_name="Cuenta de Integración",
        null=True,
        blank=True
    )
    
    metric_key = models.CharField(max_length=100, verbose_name="Clave de la métrica")
    metric_name = models.CharField(max_length=255, verbose_name="Nombre de la métrica")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    # Orden de visualización en el reporte
    display_order = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Métrica Seleccionada"
        verbose_name_plural = "Métricas Seleccionadas"
        unique_together = ['integration', 'metric_key']
        ordering = ['display_order', 'metric_key']
    
    def __str__(self):
        return f"{self.integration.display_name} - {self.metric_name}"
    
    @classmethod
    def get_available_metrics(cls, channel):
        """Retorna las métricas disponibles según el canal."""
        metrics_map = {
            'google_ads': cls.GOOGLE_ADS_METRICS,
            'ga4': cls.GA4_METRICS,
            'meta_ads': cls.META_ADS_METRICS,
        }
        return metrics_map.get(channel, [])


# ============================================================
# MODELO DE COMPATIBILIDAD (DEPRECATED)
# ============================================================
# Mantenemos ClientIntegration temporalmente para la migración
# TODO: Eliminar después de migrar todos los datos existentes

class ClientIntegration(models.Model):
    """
    [DEPRECATED] - Usar IntegrationAccount en su lugar.
    
    Este modelo se mantiene solo para compatibilidad con migraciones existentes.
    Será eliminado en una versión futura.
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
        related_name='old_integrations',
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
    
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    
    google_ads_customer_id = models.CharField(max_length=50, blank=True, null=True)
    ga4_property_id = models.CharField(max_length=50, blank=True, null=True)
    
    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "[DEPRECATED] Integración de Cliente"
        verbose_name_plural = "[DEPRECATED] Integraciones de Clientes"
    
    def __str__(self):
        return f"[DEPRECATED] {self.client.name} - {self.get_integration_type_display()}"
    
    def is_token_expired(self):
        if not self.token_expiry:
            return True
        return timezone.now() >= self.token_expiry


# ============================================================
# REPORT LOG
# ============================================================

class ReportLog(models.Model):
    """
    Registra cada relatório gerado e enviado.
    Serve como histórico de envios e para auditoria/debug.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('partial', 'Enviado parcialmente'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='report_logs',
        verbose_name="Cliente"
    )
    message_generated = models.TextField(verbose_name="Mensaje generado")
    sent_at = models.DateTimeField(auto_now_add=True)
    channel_used = models.CharField(max_length=10, verbose_name="Canal usado")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )

    # Status detalhado por canal
    email_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Estado email"
    )
    whatsapp_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Estado WhatsApp"
    )
    error_detail = models.TextField(blank=True, null=True, verbose_name="Detalle del error")

    # Snapshot das métricas usadas (para auditoria)
    metrics_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Snapshot de métricas"
    )

    # Score de saúde da campanha gerado pela IA (0–100)
    campaign_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Score de campaña"
    )
    score_reason = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Motivo del score"
    )

    class Meta:
        verbose_name = "Log de Reporte"
        verbose_name_plural = "Logs de Reportes"
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.client.name} - {self.sent_at.strftime('%d/%m/%Y %H:%M')} - {self.get_status_display()}"


# ============================================================
# CLIENT METRIC CONFIG
# ============================================================

# Métricas padrão criadas para todo novo cliente
DEFAULT_METRICS = {
    'google_ads': [
        ('clicks',       'Clics',          0),
        ('cpc',          'CPC',            1),
        ('conversions',  'Conversiones',   2),
        ('spend',        'Inversión',      3),
    ],
    'ga4': [
        ('sessions',     'Sesiones',       0),
        ('users',        'Usuarios',       1),
        ('bounce_rate',  'Tasa de rebote', 2),
    ],
    'meta_ads': [
        ('reach',        'Alcance',        0),
        ('cpm',          'CPM',            1),
        ('ctr',          'CTR',            2),
        ('conversions',  'Leads',          3),
    ],
}


class ClientMetricConfig(models.Model):
    """
    Define quais métricas de cada plataforma aparecem no dashboard público do cliente.
    A agência pode ativar/desativar, renomear e reordenar cada métrica por cliente.
    """
    PLATFORM_CHOICES = [
        ('google_ads', 'Google Ads'),
        ('ga4', 'Google Analytics 4'),
        ('meta_ads', 'Meta Ads'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='metric_configs',
        verbose_name="Cliente"
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name="Plataforma"
    )
    metric_key = models.CharField(
        max_length=50,
        verbose_name="Clave de métrica",
        help_text="Ex: clicks, cpc, conversions, spend, sessions, bounce_rate"
    )
    display_name = models.CharField(
        max_length=80,
        verbose_name="Nombre en el dashboard",
        help_text="Ex: Clics, CPC, Conversiones"
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Visible en el dashboard"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Orden"
    )

    class Meta:
        verbose_name = "Configuración de Métrica"
        verbose_name_plural = "Configuraciones de Métricas"
        ordering = ['platform', 'order']
        unique_together = ['client', 'platform', 'metric_key']

    def __str__(self):
        return f"{self.client.name} / {self.get_platform_display()} / {self.display_name}"


def _create_default_metric_configs(client):
    """Cria as métricas padrão para um cliente recém-criado."""
    configs = []
    for platform, metrics in DEFAULT_METRICS.items():
        for metric_key, display_name, order in metrics:
            configs.append(ClientMetricConfig(
                client=client,
                platform=platform,
                metric_key=metric_key,
                display_name=display_name,
                order=order,
                is_visible=True,
            ))
    ClientMetricConfig.objects.bulk_create(configs, ignore_conflicts=True)


@receiver(post_save, sender=Client)
def create_metric_configs_for_new_client(sender, instance, created, **kwargs):
    """Signal: cria configurações de métricas padrão ao criar um novo cliente."""
    if created:
        _create_default_metric_configs(instance)

