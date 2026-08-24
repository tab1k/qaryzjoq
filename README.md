# QARYZ JOQ — лендинг

Django 6 + gunicorn + WhiteNoise. Одностраничник с калькулятором платежа, модальной формой заявки и админкой для заявок.

```
.
├── Dockerfile              сборка образа (python 3.12-slim, pip)
├── requirements.txt        зафиксированные зависимости (генерируется из uv.lock)
├── docker-compose.yml      запуск на сервере
├── docker-entrypoint.sh    миграции → статика → суперпользователь → gunicorn
├── .env.example            шаблон переменных окружения
└── src/
    ├── config/             настройки, urls, wsgi
    ├── landing/            приложение лендинга (модель Lead, форма, вьюха, админка)
    ├── static/             css, js, изображения, логотипы
    └── templates/          base.html + landing/index.html
```

## Локальный запуск

```bash
uv sync
cp .env.example .env          # для локальной работы достаточно DJANGO_DEBUG=True
uv run src/manage.py migrate
uv run src/manage.py createsuperuser
uv run src/manage.py runserver
```

Сайт: http://127.0.0.1:8000/ · Админка: http://127.0.0.1:8000/admin/

## Деплой на сервер

```bash
git clone <репозиторий> qaryz_joq && cd qaryz_joq

cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # ключ в DJANGO_SECRET_KEY
nano .env                     # домен, ключ, пароль суперпользователя

docker compose up -d --build
docker compose logs -f web    # миграции, сборка статики, старт gunicorn
```

Контейнер слушает `127.0.0.1:8000`. База (SQLite) лежит в docker-томе `db-data`, статика собирается внутрь образа при старте — пересборка данные не трогает.

### Обязательные переменные в `.env`

| Переменная | Назначение |
|---|---|
| `DJANGO_SECRET_KEY` | длинный случайный ключ |
| `DJANGO_DEBUG` | `False` на проде |
| `DJANGO_ALLOWED_HOSTS` | `qaryzjoq.kz,www.qaryzjoq.kz` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | те же домены **со схемой** `https://` |
| `DJANGO_USE_HTTPS` | `True` **после** того как заработает сертификат |
| `DJANGO_SUPERUSER_PASSWORD` | задать, чтобы админ создался при первом старте |

`DJANGO_USE_HTTPS=True` включает редирект на https, HSTS и secure-куки. Пока сертификата нет — оставьте `False`, иначе в админку не зайти.

### nginx перед контейнером

```nginx
server {
    listen 80;
    server_name qaryzjoq.kz www.qaryzjoq.kz;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Далее `certbot --nginx -d qaryzjoq.kz -d www.qaryzjoq.kz`, после чего в `.env` ставим `DJANGO_USE_HTTPS=True` и `docker compose up -d`.

### Если менялись зависимости

`requirements.txt` собирается из `uv.lock`, обновлять так:

```bash
uv lock
uv export --frozen --no-dev --no-emit-project --format requirements.txt -o requirements.txt
```

## Обновление

```bash
git pull
docker compose up -d --build
```

Миграции и `collectstatic` выполняются автоматически при старте контейнера.

## Полезные команды

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate
docker compose logs -f web

# бэкап базы
docker compose cp web:/data/db.sqlite3 ./backup-$(date +%F).sqlite3
```

## Заявки

Модель `landing.Lead`: имя, телефон, сумма долга, сообщение, статус (новая / в работе / обработана) и данные расчёта из калькулятора (сумма кредитов, платежи, доход, новый платёж). Смотреть и вести — в админке, раздел «Заявки».

Письма проект не отправляет. Если нужны уведомления на почту — заполните `EMAIL_HOST` и остальные `EMAIL_*` в `.env`.

## PostgreSQL вместо SQLite

Раскомментируйте `POSTGRES_*` в `.env`, добавьте сервис `db` в `docker-compose.yml` и `psycopg[binary]` в зависимости — настройки подхватят Postgres автоматически.
