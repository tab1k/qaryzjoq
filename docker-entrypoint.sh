#!/bin/sh
set -e

# ждём базу, если используется PostgreSQL
if [ -n "$POSTGRES_DB" ]; then
  echo "→ Ожидание PostgreSQL"
  for i in $(seq 1 30); do
    python -c "
import os, socket, sys
s = socket.socket()
s.settimeout(2)
try:
    s.connect((os.environ.get('POSTGRES_HOST', 'db'), int(os.environ.get('POSTGRES_PORT', 5432))))
except OSError:
    sys.exit(1)
" && break
    sleep 2
  done
fi

echo "→ Миграции"
python manage.py migrate --noinput

echo "→ Сборка статики"
python manage.py collectstatic --noinput --clear

# суперпользователь создаётся только если задан пароль и его ещё нет
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "→ Проверка суперпользователя"
  python manage.py createsuperuser --noinput 2>/dev/null && \
    echo "  создан: $DJANGO_SUPERUSER_USERNAME" || \
    echo "  уже существует, пропускаем"
fi

if [ "$1" = "gunicorn" ]; then
  echo "→ Запуск gunicorn на порту ${GUNICORN_PORT:-8000}"
  exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${GUNICORN_PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
fi

exec "$@"
