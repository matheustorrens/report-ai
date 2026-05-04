---
description: Padrões Django reutilizáveis para o projeto ReportAI.
---

# Skill: Django Patterns — ReportAI

Padrões reutilizáveis ajustados à estrutura atual do projeto.

## Modelo de Dados Atual (NÃO usar BaseModel abstrato)
```python
# O projeto NÃO usa BaseModel abstrato com UUID para todos os models.
# Client usa BigAutoField (default Django), IntegrationAccount usa UUID.
# Manter essa convenção — não forçar UUID em models que não precisam.

# reportai/models.py — exemplo de novo model
class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
```

## Service Layer Pattern
```python
# reportai/services/<nome>.py
import logging

logger = logging.getLogger(__name__)

class ExampleService:
    """Descrição em português brasileiro."""

    def __init__(self, user):
        self.user = user

    def execute(self):
        """Executa a lógica de negócio."""
        ...
```

## View Pattern — Function-Based (padrão atual)
```python
# reportai/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

@login_required
def example_view(request):
    """Descrição em português brasileiro."""
    items = Item.objects.filter(
        owner=request.user  # SEMPRE filtrar pelo usuário
    ).select_related('related_model')
    
    return render(request, 'reportai/example.html', {'items': items})
```

## View Pattern — Class-Based (migração gradual)
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class ExampleListView(LoginRequiredMixin, ListView):
    """Descrição em português brasileiro."""
    template_name = 'reportai/example_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        return Item.objects.filter(
            owner=self.request.user
        ).select_related('related_model')
```

## Query Pattern — Sempre Otimizar
```python
# ERRADO
clients = Client.objects.filter(owner=user)
for client in clients:
    integrations = client.integrations.all()  # N+1 query!

# CORRETO
clients = Client.objects.filter(owner=user).prefetch_related(
    'integrations',
    'integrations__selected_campaigns',
    'integrations__selected_metrics'
)
```

## API View Pattern (sem DRF — usando JsonResponse)
```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_POST
def api_example(request):
    """Endpoint que recebe JSON e retorna JSON."""
    try:
        data = json.loads(request.body)
        # validar e processar
        return JsonResponse({'status': 'ok', 'data': result})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error("Erro no api_example: %s", e)
        return JsonResponse({'error': 'Erro interno'}, status=500)
```

## Template Pattern
```html
{% extends "reportai/base.html" %}
{% load static %}

{% block title %}Título em Espanhol{% endblock %}

{% block content %}
<div class="page-header">
    <h1>Título em Espanhol</h1>
</div>

{% if messages %}
<div class="messages">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}
</div>
{% endif %}

<div class="page-content">
    {% for item in items %}
    <div class="card">
        <h3>{{ item.name }}</h3>
        <a href="{% url 'reportai:item_detail' item.id %}">Ver detalle</a>
    </div>
    {% empty %}
    <p>No hay elementos todavía.</p>
    {% endfor %}
</div>
{% endblock %}
```
