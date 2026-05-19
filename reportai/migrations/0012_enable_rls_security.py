# Migration de segurança: habilita Row Level Security (RLS) em todas as tabelas
# do schema public no Supabase/PostgreSQL.
#
# CONTEXTO:
# O Supabase expõe o schema public via PostgREST (REST API). Sem RLS, qualquer
# pessoa com a URL pública do projeto pode ler, editar e apagar todos os dados.
# Esta migration corrige dois alertas críticos detectados pelo Supabase Security Advisor:
#
#   - rls_disabled_in_public  (check 0013): tabelas sem RLS habilitado
#   - sensitive_columns_exposed (check 0023): colunas sensíveis (access_token,
#     refresh_token, email, password) acessíveis sem restrições
#
# ESTRATÉGIA:
# Como o Django se conecta diretamente ao PostgreSQL via psycopg2 (role postgres/
# service_role), ele bypassa o RLS por padrão. Habilitar RLS sem criar policies
# para anon/authenticated bloqueia APENAS o acesso via API REST do Supabase,
# sem afetar o funcionamento normal do Django.
#
# EXECUÇÃO:
# - Em PostgreSQL (Supabase produção): aplica ALTER TABLE ... ENABLE ROW LEVEL SECURITY
# - Em SQLite (desenvolvimento local): operação ignorada com segurança

from django.db import migrations


# Tabelas da app reportai
REPORTAI_TABLES = [
    "reportai_client",               # contém email (sensitive_columns_exposed)
    "reportai_clientintegration",    # DEPRECATED - contém access_token, refresh_token
    "reportai_integrationaccount",   # contém access_token, refresh_token (crítico)
    "reportai_selectedcampaign",
    "reportai_selectedmetric",
    "reportai_reportlog",
    "reportai_clientmetricconfig",
    "reportai_agencyprofile",
    "reportai_timelineentry",
]

# Tabelas da app landing
LANDING_TABLES = [
    "landing_waitlistentry",         # contém email (sensitive_columns_exposed)
]

# Tabelas do Django core (no schema public do Supabase)
DJANGO_SYSTEM_TABLES = [
    "auth_user",                     # contém password (hash), email — crítico
    "auth_group",
    "auth_permission",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_session",                # contém session_data — crítico
    "django_content_type",
    "django_migrations",
    "django_admin_log",
]

ALL_TABLES = REPORTAI_TABLES + LANDING_TABLES + DJANGO_SYSTEM_TABLES


def enable_rls(apps, schema_editor):
    """Habilita RLS em todas as tabelas públicas no Supabase/PostgreSQL."""
    if schema_editor.connection.vendor != "postgresql":
        # SQLite (desenvolvimento local) não suporta RLS — ignorar sem erro
        return

    for table in ALL_TABLES:
        schema_editor.execute(
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"
        )


def disable_rls(apps, schema_editor):
    """Reverte o RLS (rollback) — desabilita em todas as tabelas."""
    if schema_editor.connection.vendor != "postgresql":
        return

    for table in ALL_TABLES:
        schema_editor.execute(
            f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("reportai", "0011_agencyprofile_legal_acceptance"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
