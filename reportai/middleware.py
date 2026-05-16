"""
Middleware temporário de profiling de performance.
Ativo APENAS quando DEBUG=True.

REMOVER (ou comentar o bloco 'if DEBUG' no settings.py) antes do deploy para produção.
"""

import time
import logging

from django.db import connection

perf = logging.getLogger('reportai.perf')


class TimingMiddleware:
    """
    Intercepta cada requisição HTTP e loga:
    - Tempo total de resposta
    - Número de queries SQL executadas
    - Tempo total gasto em SQL
    - Tempo gasto fora do SQL (Python puro + chamadas externas)

    Nota: connection.queries só é populado quando DEBUG=True no Django.
    Em produção (DEBUG=False), este middleware é seguro mas não coleta dados de queries.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Captura o índice atual do log de queries antes de processar
        # para isolar apenas as queries desta requisição
        queries_before = len(connection.queries)

        t0 = time.perf_counter()
        response = self.get_response(request)
        elapsed = time.perf_counter() - t0

        # Queries executadas APENAS nesta requisição
        queries_this_request = connection.queries[queries_before:]
        n_queries = len(queries_this_request)
        sql_time = sum(float(q.get('time', 0)) for q in queries_this_request)
        python_time = elapsed - sql_time

        # Identifica se esta rota faz chamadas externas (baseado no path)
        external_flag = _flag_external_calls(request.path)

        perf.debug(
            '| %-6s %-50s → %d | total=%.3fs | queries=%2d | SQL=%.3fs | Python=%.3fs%s',
            request.method,
            request.path[:50],
            response.status_code,
            elapsed,
            n_queries,
            sql_time,
            python_time,
            external_flag,
        )

        return response


def _flag_external_calls(path):
    """
    Retorna uma string de aviso se a rota conhecidamente dispara APIs externas.
    Baseado em análise estática de views.py — não mede o tempo das chamadas,
    apenas sinaliza a presença para correlação manual.
    """
    external_routes = {
        '/app/reports/generate/': ' [⚠ Groq+GA4+GoogleAds]',
        '/api/report-preview/':   ' [⚠ Groq+GA4+GoogleAds]',
        '/oauth/callback':         ' [⚠ Google OAuth]',
        '/app/oauth/start/':       ' [⚠ Google OAuth]',
    }
    for prefix, label in external_routes.items():
        if path.startswith(prefix):
            return label
    return ''
