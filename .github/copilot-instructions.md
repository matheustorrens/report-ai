## SEMPRE ME RESPONDA EM PORTUGUÊS!!!

# ReportAI — Contexto Global do Projeto

## O Que é o ReportAI
SaaS que automatiza o envio de relatórios semanais (toda segunda-feira) para clientes de agências de marketing espanholas e freelancers espanhóis. Os relatórios consolidam dados de Google Ads, Meta Ads e GA4, enviados via WhatsApp (Evolution API) e e-mail (Resend), de forma humanizada com IA (Grok).

## Stack Técnica
- **Backend**: Python 3.x + Django (SEMPRE use recursos nativos do Django antes de bibliotecas externas)
- **Banco de dados**: SQLite em desenvolvimento, Supabase (PostgreSQL) em produção — usar `dj_database_url` para configuração
- **ORM**: Django ORM nativo — nunca abrir conexões psycopg2 diretamente
- **Task Queue**: Celery + Redis (quando configurado)
- **Autenticação**: Django Auth nativo (model `User` usado diretamente como "agência")
- **Frontend**: Django Templates + CSS customizado + JavaScript vanilla + GSAP (animações)
- **Hospedagem**: Gunicorn (Procfile configurado)
- **Integrações externas**: Google Ads API, Meta Ads API, GA4 (Google Analytics Data API), Evolution API (WhatsApp), Resend (e-mail), Grok (geração de texto humanizado)
- **Landing page / waitlist**: getreportai.com → e-mails armazenados no Supabase
- **Arquivos estáticos**: WhiteNoise (CompressedManifestStaticFilesStorage)

## Estrutura de Diretórios Base
```
v1 (02-04-26)/
├── manage.py
├── requirements.txt
├── Procfile
├── core/                   # settings, urls, wsgi, asgi (config do projeto Django)
├── landing/                # app: landing page pública + waitlist
├── reportai/               # app principal: clientes, integrações, relatórios, dashboard
├── templates/              # todos os templates Django
├── static/                 # CSS, JS, imagens
├── .github/
│   ├── agents/             # agentes Copilot
│   └── skills/             # skills reutilizáveis
└── materiais_para_ia/      # documentação de referência (não é código)
```
**IMPORTANTE**: A estrutura pode evoluir. Antes de agir, sempre leia os arquivos relevantes para confirmar a estrutura atual.

## Modelo de Dados Fundamental
- `User` (Django auth) → N `Client` → N `IntegrationAccount` (por canal) → N `SelectedCampaign` + N `SelectedMetric`
- **NÃO existe model `Agency`** — o `User` representa a agência diretamente
- `Client.owner` é ForeignKey para `User`
- Um cliente pode ter múltiplas contas do mesmo canal (ex: 2 contas Google Ads)
- **Antes de criar novos models**, leia `reportai/models.py` para verificar o que já existe

## Protocolo Obrigatório — Antes de Qualquer Ação
1. **Leia os arquivos relevantes** antes de modificar qualquer coisa — nunca assuma o estado do código
2. **Verifique o que já existe** — não reimplemente funcionalidades que já foram criadas
3. **Consulte `requirements.txt`** antes de sugerir bibliotecas — pode já estar instalada
4. **Leia `core/settings.py`** para entender a configuração atual (apps instaladas, middleware, etc.)
5. **Leia `reportai/urls.py`** para verificar URLs existentes antes de criar novas

## Convenções Obrigatórias de Código
1. Nomes em inglês para models, views, funções e variáveis
2. Comentários e docstrings em português brasileiro (para manutenção do dev)
3. Toda view que acessa banco usa Django ORM — nunca raw SQL sem justificativa
4. Toda chamada a API externa deve ter try/except com logging estruturado
5. Migrations sempre revisadas antes de aplicar — nunca alterar migrations já aplicadas em produção
6. Variáveis sensíveis SEMPRE via `os.environ.get()` — nunca hardcoded
7. `{% csrf_token %}` em todo formulário POST nos templates
8. `{% url 'namespace:name' %}` em vez de URLs hardcoded nos templates

## URLs Principais
- `/` → Landing page (home)
- `/app/login/` → Login
- `/app/register/` → Registro
- `/app/dashboard/` → Dashboard principal
- `/app/clients/` → Lista de clientes
- `/app/integrations/` → Gestão de integrações
- `/app/reports/` → Histórico de relatórios
- `/app/oauth/start/<channel>/` → Início do fluxo OAuth
- `/oauth/callback` → Callback OAuth (nível raiz)
- `/admin/` → Admin Django

## Idioma
- Código, nomes de variáveis, models, URLs: **inglês**
- Comentários e docstrings: **português brasileiro**
- Interface do usuário (templates): **espanhol** (mercado alvo é Espanha)
- Landing page: **espanhol**
