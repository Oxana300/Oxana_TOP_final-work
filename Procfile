release: python manage.py migrate --noinput
web: gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4