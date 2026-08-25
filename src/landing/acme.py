"""Подтверждение домена для Let's Encrypt через HTTP.

Сертификат выпускается вне сервера (из-за перехвата TLS провайдером),
поэтому проверочный ответ отдаёт само приложение: значение кладётся
в переменную окружения ACME_CHALLENGE в формате «токен.отпечаток».
"""

import os

from django.http import Http404, HttpResponse


def acme_challenge(request, token):
    value = os.environ.get('ACME_CHALLENGE', '').strip()

    if not value or not value.startswith(f'{token}.'):
        raise Http404('Проверочный код не задан')

    return HttpResponse(value, content_type='text/plain')
