"""
Настройки проекта QARYZ JOQ.

Значения, зависящие от окружения, берутся из переменных среды (файл .env).
"""

import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse, reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent


def load_dotenv(path: Path) -> None:
    """Простейший загрузчик .env: переменные окружения имеют приоритет."""
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(PROJECT_DIR / '.env')


def env(name: str, default: str = '') -> str:
    value = os.environ.get(name)
    return default if value is None else value


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in env(name, default).split(',') if item.strip()]


def env_path(name: str, default: Path) -> Path:
    """Путь из переменной окружения.

    Если каталога назначения нет (например, продовый .env с путями контейнера
    открыли на локальной машине) — используем значение по умолчанию.
    """
    value = env(name)
    if not value:
        return default
    path = Path(value)
    return path if path.parent.exists() else default


# --- базовое ---------------------------------------------------------------

SECRET_KEY = env('DJANGO_SECRET_KEY', 'django-insecure-dev-key-only-for-local-use')

DEBUG = env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'go.qaryzjoq.kz,qaryzjoq.kz,www.qaryzjoq.kz,31.14.27.130,localhost,127.0.0.1,qaryzjoq-web,web')
for _h in ('go.qaryzjoq.kz', 'qaryzjoq.kz', 'www.qaryzjoq.kz', 'localhost', '127.0.0.1', 'qaryzjoq-web', 'web'):
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)

# схему указывать обязательно: https://go.qaryzjoq.kz
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS', 'https://go.qaryzjoq.kz,http://go.qaryzjoq.kz,https://qaryzjoq.kz')
for _o in ('https://go.qaryzjoq.kz', 'http://go.qaryzjoq.kz', 'https://qaryzjoq.kz'):
    if _o not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_o)

# --- интеграция Bitrix24 (CRM) ---------------------------------------------
BITRIX24_WEBHOOK_URL = env('BITRIX24_WEBHOOK_URL', 'https://qaryzjoq.bitrix24.kz/rest/1/y9rcz9ysnx1ukyh7/')


# --- приложения ------------------------------------------------------------

INSTALLED_APPS = [
    # тема админки — строго до django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'landing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- админка ---------------------------------------------------------------

UNFOLD = {
    'SITE_TITLE': 'QARYZ JOQ',
    'SITE_ICON': lambda request: static('brand/logo-mark.png'),
    'SITE_LOGO': lambda request: static('brand/logo-lockup.png'),
    'SITE_FAVICONS': [
        {'rel': 'icon', 'sizes': '32x32', 'type': 'image/png', 'href': lambda request: static('brand/logo-mark.png')},
    ],
    'LOGIN': {
        'image': lambda request: static('img/Mask group.png'),
    },
    'SITE_HEADER': 'QARYZ JOQ — заявки',
    'SITE_SUBHEADER': 'Панель управления сайтом',
    'SITE_URL': '/',
    'SITE_SYMBOL': 'request_quote',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    'COLORS': {
        # фирменный зелёный в оттенках, которые ждёт тема
        'primary': {
            '50': '236 247 240',
            '100': '209 236 219',
            '200': '166 218 187',
            '300': '117 197 152',
            '400': '61 166 111',
            '500': '5 130 64',
            '600': '4 108 53',
            '700': '4 88 44',
            '800': '4 61 32',
            '900': '3 42 22',
            '950': '2 26 14',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': 'Заявки',
                'items': [
                    {
                        'title': 'Все заявки',
                        'icon': 'inbox',
                        'link': reverse_lazy('admin:landing_lead_changelist'),
                    },
                    {
                        'title': 'Новые',
                        'icon': 'mark_email_unread',
                        'link': lambda request: reverse('admin:landing_lead_changelist') + '?status__exact=new',
                    },
                    {
                        'title': 'В работе',
                        'icon': 'pending_actions',
                        'link': lambda request: reverse('admin:landing_lead_changelist') + '?status__exact=in_work',
                    },
                ],
            },
            {
                'title': 'Доступ',
                'separator': True,
                'items': [
                    {
                        'title': 'Пользователи',
                        'icon': 'person',
                        'link': reverse_lazy('admin:auth_user_changelist'),
                    },
                    {
                        'title': 'Группы',
                        'icon': 'group',
                        'link': reverse_lazy('admin:auth_group_changelist'),
                    },
                ],
            },
        ],
    },
    'DASHBOARD_CALLBACK': 'landing.dashboard.dashboard_callback',
}


# --- база данных -----------------------------------------------------------
# По умолчанию SQLite. Файл выносится в отдельный каталог, чтобы пережить
# пересборку контейнера (в docker-compose он смонтирован томом).

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env_path('DJANGO_DB_PATH', BASE_DIR / 'db.sqlite3'),
        'OPTIONS': {'timeout': 20},
    }
}

if env('POSTGRES_DB'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER', 'postgres'),
        'PASSWORD': env('POSTGRES_PASSWORD', ''),
        'HOST': env('POSTGRES_HOST', 'db'),
        'PORT': env('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- пароли ----------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- локализация -----------------------------------------------------------

LANGUAGE_CODE = 'ru'
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Asia/Almaty'
USE_I18N = True
USE_TZ = True


# --- статика ---------------------------------------------------------------

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = env_path('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30


# --- почта -----------------------------------------------------------------

if env('EMAIL_HOST'):
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'HOST': env('EMAIL_HOST'),
            'PORT': int(env('EMAIL_PORT', '587')),
            'USERNAME': env('EMAIL_HOST_USER'),
            'PASSWORD': env('EMAIL_HOST_PASSWORD'),
            'USE_TLS': env_bool('EMAIL_USE_TLS', True),
        },
    }
else:
    # писем проект пока не шлёт: заявки складываются в базу и видны в админке
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.console.EmailBackend',
        },
    }

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'noreply@qaryzjoq.kz')


# --- безопасность ----------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# включать после того, как домен заработает по https
USE_HTTPS = env_bool('DJANGO_USE_HTTPS', False)

SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365 if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS


# --- логи ------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', 'INFO')},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
