FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Зависимости отдельным слоем — кешируются между сборками.
#
# --trusted-host нужен там, где провайдер перехватывает TLS и pip не может
# проверить сертификат pypi.org. Целостность пакетов при этом гарантируют
# sha256-хеши из requirements.txt: подменённый файл просто не установится.
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes \
        --trusted-host pypi.org \
        --trusted-host files.pythonhosted.org \
        --trusted-host pypi.python.org \
        -r requirements.txt

COPY src ./src
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# каталог для файла базы (в compose монтируется томом)
RUN mkdir -p /data && \
    adduser --system --group --no-create-home app && \
    chown -R app:app /app /data

USER app

WORKDIR /app/src

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application"]
