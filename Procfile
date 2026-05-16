web: gunicorn core.wsgi:application --workers 2 --threads 2 --worker-class gthread --timeout 120 --max-requests 1000 --bind 0.0.0.0:$PORT
