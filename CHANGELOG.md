# Changelog — ReportAI

## [Unreleased] — 04/05/2026

### Novo

#### Sistema de Autenticação Completo
- `login_view`: autenticação real via `authenticate()` + `auth_login()`, com lookup por e-mail
- `register_view`: criação de usuário com nome da agência, e-mail, senha e confirmação; username gerado automaticamente com fallback incremental
- `logout_view`: agora chama `auth_logout(request)` corretamente
- Templates `login.html` e `register.html`: exibem mensagem de erro inline via `{{ error }}`
- `auth.js`: substituído mock com redirect falso para submit nativo do formulário Django

#### Fluxo Pós-Criação de Cliente (PARTE 1)
- `api_create_client` retorna `profile_url` = `/app/clients/{id}/?onboarding=1`
- `list.html`: após criar cliente, redireciona para o perfil em vez de recarregar a lista
- `profile.html`: modal de onboarding "¡Cliente creado con éxito!" exibido quando `?onboarding=1` está na URL; URL limpa com `history.replaceState` após exibição

#### Perfil do Cliente com Abas (PARTE 3)
- `profile.html` reescrito com abas: "Historial de Reportes" e "Métricas"
- Aba Métricas: exibe estado vazio se não há integrações conectadas; caso contrário, mostra formulário inline de configuração de métricas
- Redirect após salvar métricas volta para a aba Métricas do perfil (`?tab=metrics`)
- Campo hidden `next` no formulário de métricas controla redirect pós-save

#### Métricas Editáveis no Relatório (PARTE 4)
- Nova view `api_client_metrics` (`GET /app/api/clients/{id}/metrics/`): retorna métricas visíveis agrupadas por plataforma com valores mockados
- `generate.html`: Step 3 "Métricas (editables)" — painel carregado via JS ao selecionar cliente; inputs editáveis por métrica
- Preview do relatório inclui `metrics_override` no payload se o usuário editou algum valor
- `api_report_preview`: aceita e repassa `metrics_override` ao Groq

#### Dashboard Público com Tabs (PARTE 5)
- `public_dashboard.html`: seção "Desglose por plataforma" com tabs CSS/JS puro
- Uma tab por plataforma presente no `metrics_snapshot` do último relatório
- Primeira tab ativa por padrão; clique alterna conteúdo sem reload

### Alterado

#### Integrações (PARTE 2)
- `integrations.html`: removido contador de métricas e botão "Métricas" de cada conta de integração

#### Segurança — Multi-tenant
- Todas as views protegidas com `@login_required`
- Todas as queries filtradas por `owner=request.user`
- `api_update_client` e `api_delete_client`: adicionado `owner=request.user` no `get_object_or_404`

#### Models
- `ClientMetricConfig`: novo model para configuração de métricas por cliente/plataforma
- `ReportLog`: campo `metrics_snapshot` (JSONField) para snapshot dos dados usados no relatório
- `Client`: campos `knowledge_level`, `next_report_at`, `dashboard_token`
- Signal `post_save` em `Client` cria `ClientMetricConfig` padrão automaticamente

#### Serviços
- `groq_service.py`: `generate_report_message` aceita `metrics` como override opcional
- `email_service.py`, `whatsapp_service.py`: criados em `reportai/services/`

### Corrigido

- `profile.html`: fragmento HTML órfão com tags `{% elif %}` fora do bloco causava `TemplateSyntaxError` — removido
- `integrations.html`: `<div class="stat">` com `{% endif %}` órfão (resto da remoção de Métricas) — removido
- `auth.js`: redirect para `/app/onboarding/integrations/` (URL inexistente) substituído por submit nativo
- `client_metrics_config_view`: redirect pós-save agora volta ao perfil do cliente em vez de página standalone
- `settings.py`: `LOGIN_URL = '/app/login/'` configurado

### Migrations

- `0002_integrationaccount_customer_hierarchy`
- `0003_client_knowledge_level_client_next_report_at_and_more`
- `0004_client_dashboard_token`
- `0005_reportlog_campaign_score`
- `0006_clientmetricconfig`
