from django.contrib import admin

from .models import Client, IntegrationAccount, SelectedCampaign, SelectedMetric, ReportLog


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
