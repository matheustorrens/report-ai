from django.db import migrations, models
import django.db.models.deletion


def populate_metric_configs(apps, schema_editor):
    """Cria configurações de métricas padrão para todos os clientes existentes."""
    Client = apps.get_model('reportai', 'Client')
    ClientMetricConfig = apps.get_model('reportai', 'ClientMetricConfig')

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

    configs_to_create = []
    for client in Client.objects.all():
        for platform, metrics in DEFAULT_METRICS.items():
            for metric_key, display_name, order in metrics:
                configs_to_create.append(ClientMetricConfig(
                    client=client,
                    platform=platform,
                    metric_key=metric_key,
                    display_name=display_name,
                    order=order,
                    is_visible=True,
                ))
    ClientMetricConfig.objects.bulk_create(configs_to_create, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ('reportai', '0005_reportlog_campaign_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientMetricConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(
                    choices=[('google_ads', 'Google Ads'), ('ga4', 'Google Analytics 4'), ('meta_ads', 'Meta Ads')],
                    max_length=20,
                    verbose_name='Plataforma'
                )),
                ('metric_key', models.CharField(
                    help_text='Ex: clicks, cpc, conversions, spend, sessions, bounce_rate',
                    max_length=50,
                    verbose_name='Clave de métrica'
                )),
                ('display_name', models.CharField(
                    help_text='Ex: Clics, CPC, Conversiones',
                    max_length=80,
                    verbose_name='Nombre en el dashboard'
                )),
                ('is_visible', models.BooleanField(default=True, verbose_name='Visible en el dashboard')),
                ('order', models.IntegerField(default=0, verbose_name='Orden')),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='metric_configs',
                    to='reportai.client',
                    verbose_name='Cliente'
                )),
            ],
            options={
                'verbose_name': 'Configuración de Métrica',
                'verbose_name_plural': 'Configuraciones de Métricas',
                'ordering': ['platform', 'order'],
                'unique_together': {('client', 'platform', 'metric_key')},
            },
        ),
        migrations.RunPython(populate_metric_configs, migrations.RunPython.noop),
    ]
