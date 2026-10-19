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

echo "→ Проверка суперпользователя"
python manage.py ensure_superuser

if [ "$1" = "gunicorn" ]; then
  echo "→ Запуск gunicorn на порту ${GUNICORN_PORT:-8000}"
  exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${GUNICORN_PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --worker-class sync \
    --timeout 60 \
    --max-requests 2000 \
    --max-requests-jitter 200 \
    --access-logfile - \
    --error-logfile -
fi

exec "$@"
