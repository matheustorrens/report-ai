from django.db import migrations, models


def backfill_customer_fields(apps, schema_editor):
    """Preenche campos novos com dados legados para manter compatibilidade."""
    IntegrationAccount = apps.get_model('reportai', 'IntegrationAccount')

    for account in IntegrationAccount.objects.all().iterator():
        changed_fields = []

        if not account.customer_id and account.account_id:
            account.customer_id = account.account_id
            changed_fields.append('customer_id')

        if not account.customer_name and account.account_name:
            account.customer_name = account.account_name
            changed_fields.append('customer_name')

        if not account.login_customer_id:
            extra_data = account.extra_data or {}
            extra_login = extra_data.get('login_customer_id')
            if extra_login:
                account.login_customer_id = str(extra_login).replace('-', '')
                changed_fields.append('login_customer_id')

        if changed_fields:
            account.save(update_fields=changed_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('reportai', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integrationaccount',
            name='customer_id',
            field=models.CharField(
                blank=True,
                help_text='ID operacional da conta Google Ads (sem hífens)',
                max_length=100,
                null=True,
                verbose_name='Customer ID',
            ),
        ),
        migrations.AddField(
            model_name='integrationaccount',
            name='customer_name',
            field=models.CharField(
                blank=True,
                help_text='Nome descritivo da conta Google Ads',
                max_length=255,
                null=True,
                verbose_name='Customer Name',
            ),
        ),
        migrations.AddField(
            model_name='integrationaccount',
            name='login_customer_id',
            field=models.CharField(
                blank=True,
                help_text='ID da conta MCC usada no header login-customer-id',
                max_length=100,
                null=True,
                verbose_name='Login Customer ID',
            ),
        ),
        migrations.RunPython(backfill_customer_fields, migrations.RunPython.noop),
    ]
