from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reportai', '0004_client_dashboard_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportlog',
            name='campaign_score',
            field=models.IntegerField(blank=True, null=True, verbose_name='Score de campaña'),
        ),
        migrations.AddField(
            model_name='reportlog',
            name='score_reason',
            field=models.CharField(blank=True, default='', max_length=120, verbose_name='Motivo del score'),
        ),
    ]
