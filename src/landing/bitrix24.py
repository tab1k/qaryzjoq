import json
import logging
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

PROMO_CODE_REGEX = re.compile(r'\b(\d{4,8})\b')


def _format_money(amount: int | float | None) -> str:
    if amount is None:
        return ''
    try:
        return f"{int(amount):,}".replace(',', ' ') + ' ₸'
    except (ValueError, TypeError):
        return str(amount)


def _b24_call(method: str, payload: dict | None = None) -> dict | None:
    """Выполняет REST API вызов к Битрикс24 через входящий вебхук."""
    webhook_url = getattr(settings, 'BITRIX24_WEBHOOK_URL', '').strip()
    if not webhook_url:
        logger.warning("BITRIX24_WEBHOOK_URL не настроен.")
        return None

    endpoint = webhook_url.rstrip('/') + '/' + method.strip('/') + '.json'

    try:
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
        else:
            req = urllib.request.Request(endpoint)

        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                ctx_insecure = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ctx_insecure, timeout=10) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            raise
    except Exception as exc:
        logger.error("Ошибка вызова Битрикс24 API (%s): %s", method, exc)
        return None


def extract_promo_from_text(text: str | None) -> str | None:
    """Ищет промокод (набор от 4 до 8 цифр) в произвольном тексте сообщения."""
    if not text:
        return None

    # Очищаем HTML теги, если текст пришел с разметкой
    clean_text = re.sub(r'<[^>]+>', ' ', text)

    # Ищем последовательность от 4 до 8 цифр
    match = PROMO_CODE_REGEX.search(clean_text)
    if match:
        return match.group(1)
    return None


def extract_and_save_promo_for_deal(deal_id: int | str, text: str | None = None) -> dict:
    """Извлекает промокод из первого сообщения и сохраняет в поле сделки.

    Если промокод в сделке уже заполнен — повторно не перезаписывает.
    """
    if not deal_id:
        return {"ok": False, "error": "deal_id is required"}

    promo_field = getattr(settings, 'BITRIX24_PROMO_FIELD', 'UF_CRM_6A796DFB578FE')

    # 1. Получаем сделку из Битрикс24
    deal_res = _b24_call('crm.deal.get', {'id': deal_id})
    if not deal_res or 'result' not in deal_res:
        return {"ok": False, "error": f"Failed to fetch deal #{deal_id}"}

    deal_data = deal_res['result']
    existing_promo = deal_data.get(promo_field)

    # 2. Если промокод уже заполнен — не перезаписываем его
    if existing_promo:
        logger.info("В сделке #%s уже заполнен промокод: %s. Пропуск.", deal_id, existing_promo)
        return {
            "ok": True,
            "status": "already_set",
            "deal_id": deal_id,
            "promo_code": existing_promo
        }

    # 3. Ищем текст для извлечения промокода
    promo_code = None

    # А. Если текст передан прямо в запросе (из робота Б24)
    if text:
        promo_code = extract_promo_from_text(text)

    # Б. Если в переданном тексте нет — смотрим комментарий / описание сделки
    if not promo_code:
        deal_comments = deal_data.get('COMMENTS') or deal_data.get('ADDITIONAL_INFO')
        if deal_comments:
            promo_code = extract_promo_from_text(deal_comments)

    # В. Если всё ещё нет — запрашиваем дела/сообщения таймлайна сделки
    if not promo_code:
        activities = _b24_call('crm.activity.list', {
            'filter': {'OWNER_TYPE_ID': 2, 'OWNER_ID': deal_id},
            'order': {'ID': 'ASC'}
        })
        if activities and 'result' in activities:
            for act in activities['result']:
                desc = act.get('DESCRIPTION') or act.get('SUBJECT')
                promo_code = extract_promo_from_text(desc)
                if promo_code:
                    break

    # 4. Если промокод найден — записываем его в кастомное поле сделки
    if promo_code:
        update_res = _b24_call('crm.deal.update', {
            'id': deal_id,
            'fields': {
                promo_field: promo_code
            },
            'params': {'REGISTER_SONET_EVENT': 'N'}
        })

        if update_res and update_res.get('result'):
            logger.info("Успешно сохранён промокод '%s' для сделки #%s", promo_code, deal_id)
            return {
                "ok": True,
                "status": "updated",
                "deal_id": deal_id,
                "promo_code": promo_code
            }
        else:
            logger.error("Ошибка при записи промокода в сделку #%s: %s", deal_id, update_res)
            return {"ok": False, "error": f"Failed to update deal #{deal_id}"}

    logger.info("В сделке #%s промокод из 4-8 цифр не обнаружен.", deal_id)
    return {
        "ok": True,
        "status": "no_promo_found",
        "deal_id": deal_id
    }


def send_lead_to_bitrix24(lead) -> bool:
    """Отправляет созданную заявку (Lead) в Битрикс24 CRM.

    Создаёт лид с источником «Лендинг» (ID=3 в Б24), параметрами
    расчёта из калькулятора, контактами и детальным описанием.
    """
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

    title = f"Заявка с сайта: {lead.name}"
    if lead.calc_result:
        title += f" (новый платёж {_format_money(lead.calc_result)})"

    source_id = getattr(settings, 'BITRIX24_SOURCE_ID', '3')

    payload = {
        "fields": {
            "TITLE": title,
            "NAME": lead.name,
            "PHONE": [{"VALUE": str(lead.phone), "VALUE_TYPE": "WORK"}],
            "COMMENTS": comments,
            "SOURCE_ID": source_id,
            "SOURCE_DESCRIPTION": "go.qaryzjoq.kz (Калькулятор)",
            "STATUS_ID": "NEW",
            "UTM_SOURCE": "landing",
            "UTM_MEDIUM": "website",
            "UTM_CAMPAIGN": "qaryzjoq",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    if lead.calc_debt:
        try:
            payload["fields"]["OPPORTUNITY"] = float(lead.calc_debt)
            payload["fields"]["CURRENCY_ID"] = "KZT"
        except (ValueError, TypeError):
            pass

    res = _b24_call('crm.lead.add', payload)
    if res and 'result' in res:
        logger.info("Лид #%s успешно передан в Битрикс24 с источником «Лендинг»: B24_ID=%s", lead.id, res.get('result'))
        return True
    else:
        logger.warning("Битрикс24 вернул ошибку для лида #%s: %s", lead.id, res)
        return False

