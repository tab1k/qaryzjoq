"""
Интеграция с Bitrix24 через REST API (Входящий вебхук).
"""

import json
import logging
import ssl
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def _format_money(amount: int | float | None) -> str:
    if amount is None:
        return ''
    try:
        return f"{int(amount):,}".replace(',', ' ') + ' ₸'
    except (ValueError, TypeError):
        return str(amount)


def send_lead_to_bitrix24(lead) -> bool:
    """Отправляет созданную заявку (Lead) в Битрикс24 CRM.

    Создаёт лид со всеми параметрами расчёта из калькулятора,
    контактами и структурированным описанием.
    """
    webhook_url = getattr(settings, 'BITRIX24_WEBHOOK_URL', '').strip()
    if not webhook_url:
        logger.debug("BITRIX24_WEBHOOK_URL не задан, пропуск отправки в CRM.")
        return False

    endpoint = webhook_url.rstrip('/') + '/crm.lead.add.json'

    # Подготовка строк комментария со всеми деталями расчёта
    details: list[str] = []
    if lead.calc_debt:
        details.append(f"<b>Сумма кредитов:</b> {_format_money(lead.calc_debt)}")
    if lead.calc_payments:
        details.append(f"<b>Текущий платёж в месяц:</b> {_format_money(lead.calc_payments)}")
    if lead.calc_income:
        details.append(f"<b>Официальный доход:</b> {_format_money(lead.calc_income)}")
    if lead.calc_result:
        details.append(f"<b>Рассчитанный новый платёж:</b> {_format_money(lead.calc_result)}")
    if lead.debt and not lead.calc_debt:
        details.append(f"<b>Сумма долга:</b> {lead.debt}")
    if lead.message:
        details.append(f"<b>Сообщение:</b> {lead.message}")

    comments = "<br>\n".join(details) if details else "Заявка на бесплатную консультацию с сайта"

    # Заголовок лида для удобного просмотра менеджером в CRM
    title = f"Заявка с сайта: {lead.name}"
    if lead.calc_result:
        title += f" (новый платёж {_format_money(lead.calc_result)})"

    payload = {
        "fields": {
            "TITLE": title,
            "NAME": lead.name,
            "PHONE": [{"VALUE": str(lead.phone), "VALUE_TYPE": "WORK"}],
            "COMMENTS": comments,
            "SOURCE_ID": "WEB",
            "STATUS_ID": "NEW",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    # Если есть сумма долга из калькулятора, указываем её как сумму лида (KZT)
    if lead.calc_debt:
        try:
            payload["fields"]["OPPORTUNITY"] = float(lead.calc_debt)
            payload["fields"]["CURRENCY_ID"] = "KZT"
        except (ValueError, TypeError):
            pass

    try:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )

        # Контекст SSL с поддержкой корпоративных/национальных прокси
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                res = json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                ctx_insecure = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ctx_insecure, timeout=8) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
            else:
                raise

        if 'result' in res:
            logger.info("Лид #%s успешно передан в Битрикс24: B24_ID=%s", lead.id, res.get('result'))
            return True
        else:
            logger.warning("Битрикс24 вернул ошибку для лида #%s: %s", lead.id, res)
    except Exception as exc:
        logger.error("Ошибка при отправке лида #%s в Битрикс24: %s", getattr(lead, 'id', None), exc)

    return False
