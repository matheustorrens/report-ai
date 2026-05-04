import uuid
from django.db import migrations, models


def populate_dashboard_tokens(apps, schema_editor):
    """Gera um UUID único para cada cliente existente."""
    Client = apps.get_model('reportai', 'Client')
    for client in Client.objects.all():
        client.dashboard_token = uuid.uuid4()
        client.save(update_fields=['dashboard_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('reportai', '0003_client_knowledge_level_client_next_report_at_and_more'),
    ]

    operations = [
        # Etapa 1: adiciona a coluna como nullable sem constraint de unicidade
        migrations.AddField(
            model_name='client',
            name='dashboard_token',
            field=models.UUIDField(
                null=True,
                blank=True,
                editable=False,
                verbose_name='Token del dashboard público',
            ),
        ),
        # Etapa 2: popula cada linha com um UUID único
        migrations.RunPython(populate_dashboard_tokens, migrations.RunPython.noop),
        # Etapa 3: aplica not-null e unique
        migrations.AlterField(
            model_name='client',
            name='dashboard_token',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name='Token del dashboard público',
            ),
        ),
    ]
