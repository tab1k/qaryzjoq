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

По умолчанию контейнер слушает `0.0.0.0:8000`, то есть сайт сразу доступен по `http://31.14.27.130:8000`
(не забудьте `ufw allow 8000/tcp`). Когда перед ним встанет nginx — поменяйте в `docker-compose.yml`
проброс на `"127.0.0.1:8000:8000"`, чтобы порт не торчал наружу. База (SQLite) лежит в docker-томе `db-data`, статика собирается внутрь образа при старте — пересборка данные не трогает.

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

### Nginx Proxy Manager

NPM работает в своём контейнере, поэтому до сайта он должен достучаться **по имени контейнера в общей docker-сети**, а не по `127.0.0.1` — внутри контейнера NPM это он сам.

```bash
docker network create proxy                 # один раз
docker network connect proxy <контейнер-NPM>  # имя смотреть в docker ps
cd ~/qaryzjoq && docker compose up -d        # web уже подключается к proxy
```

В NPM → Proxy Hosts → Add Proxy Host:

| Поле | Значение |
|---|---|
| Domain Names | qaryzjoq.kz, www.qaryzjoq.kz |
| Scheme | http |
| Forward Hostname | `qaryzjoq-web` |
| Forward Port | `8000` |
| Block Common Exploits | включить |
| Websockets Support | не нужно |

Вкладка SSL → Request a new SSL Certificate → Force SSL + HTTP/2, согласиться с условиями Let's Encrypt.

**Чтобы сертификат выпустился, обязательно:**

1. A-запись домена указывает на `31.14.27.130` — проверить: `dig +short qaryzjoq.kz`
2. Порты 80 и 443 открыты и заняты именно контейнером NPM:
   ```bash
   ufw allow 80/tcp && ufw allow 443/tcp
   ss -tlnp | grep -E ':80 |:443 '
   ```
3. Ничего другого на 80 порту не висит (системный nginx, apache):
   ```bash
   systemctl stop nginx apache2 2>/dev/null; systemctl disable nginx apache2 2>/dev/null
   ```
4. Прокси-хост открывается по http **до** запроса сертификата — Let's Encrypt проверяет домен именно через порт 80.

После выпуска сертификата в `.env`:

```
DJANGO_USE_HTTPS=True
DJANGO_ALLOWED_HOSTS=qaryzjoq.kz,www.qaryzjoq.kz,31.14.27.130,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://qaryzjoq.kz,https://www.qaryzjoq.kz
```

и `docker compose up -d --force-recreate`. NPM передаёт `X-Forwarded-Proto`, Django это учитывает и не зациклит редиректы.

### nginx перед контейнером (альтернатива, без NPM)

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

### Если сборка падает на TLS-сертификатах

На некоторых серверах провайдер подменяет сертификаты, и pip/docker не могут
проверить цепочку (`certificate verify failed`, `certificate signed by unknown authority`).

В `Dockerfile` для pip уже указаны `--trusted-host` вместе с `--require-hashes`,
поэтому пакеты качаются даже при перехвате, а их подлинность проверяется
по sha256 из `requirements.txt`.

Посмотреть, кто выдаёт сертификат (если это прокси — имя будет незнакомым):

```bash
docker run --rm python:3.12-slim python -c \
  "import ssl,socket;c=ssl.create_default_context();c.check_hostname=False;c.verify_mode=ssl.CERT_NONE;\
s=c.wrap_socket(socket.socket(),server_hostname='pypi.org');s.connect(('pypi.org',443));print(s.getpeercert(True) and 'соединение есть')"
```

Правильное решение — добавить корневой сертификат прокси в доверенные на хосте:

```bash
cp proxy-ca.crt /usr/local/share/ca-certificates/
update-ca-certificates
systemctl restart docker
```

**План Б — собрать образ на своей машине и перенести файлом** (сеть сервера не нужна вообще):

```bash
# локально
docker build -t qaryzjoq-web .
docker save qaryzjoq-web | gzip > qaryzjoq-web.tar.gz
scp qaryzjoq-web.tar.gz root@31.14.27.130:~/qaryzjoq/

# на сервере
docker load < qaryzjoq-web.tar.gz
docker compose up -d          # build не нужен, образ уже есть
```

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
