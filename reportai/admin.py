from django.contrib import admin

from .models import AgencyProfile, Client, IntegrationAccount, SelectedCampaign, SelectedMetric, ReportLog


@admin.register(AgencyProfile)
class AgencyProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_agency_name', 'get_email', 'trial_status', 'trial_started_at', 'created_at']
    list_filter = ['trial_status']
    search_fields = ['user__first_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'trial_started_at']
    fields = [
        'user', 'whatsapp',
        'trial_status', 'trial_started_at', 'trial_notes',
        'terms_accepted_at', 'privacy_accepted_at', 'dpa_accepted_at', 'legal_version',
        'created_at', 'updated_at',
    ]

    @admin.display(description='Agência', ordering='user__first_name')
    def get_agency_name(self, obj):
        return obj.user.first_name or obj.user.username

    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'owner', 'send_channel', 'knowledge_level', 'created_at']
    list_filter = ['send_channel', 'knowledge_level']
    search_fields = ['name', 'email']


@admin.register(IntegrationAccount)
class IntegrationAccountAdmin(admin.ModelAdmin):
    list_display = ['client', 'channel', 'account_id', 'account_name', 'status', 'token_expiry']
    list_filter = ['channel', 'status']
    search_fields = ['client__name', 'account_id', 'account_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'channel_used', 'status', 'sent_at']
    list_filter = ['status', 'channel_used']
    readonly_fields = ['sent_at']
