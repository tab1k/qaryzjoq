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


def extract_and_save_promo(entity_id: int | str, entity_type: str = 'lead', text: str | None = None) -> dict:
    """Извлекает промокод из первого сообщения и сохраняет в поле лида или сделки.

    Если промокод уже заполнен — повторно не перезаписывает.
    """
    if not entity_id:
        return {"ok": False, "error": "entity_id is required"}

    entity_type = entity_type.lower()
    is_deal = (entity_type == 'deal')

    configured_field = getattr(settings, 'BITRIX24_PROMO_FIELD', 'UF_CRM_6A796DFB578FE')
    candidate_fields = [
        'UF_CRM_1786105060756',
        'UF_CRM_6A796DFB578FE',
        'UF_CRM_PROMOCODE',
        configured_field
    ]

    get_method = 'crm.deal.get' if is_deal else 'crm.lead.get'
    update_method = 'crm.deal.update' if is_deal else 'crm.lead.update'
    owner_type_id = 2 if is_deal else 1

    # 1. Получаем сущность (лид или сделку) из Битрикс24
    res = _b24_call(get_method, {'id': entity_id})
    if not res or 'result' not in res:
        return {"ok": False, "error": f"Failed to fetch {entity_type} #{entity_id}"}

    data = res['result']

    # 2. Если промокод уже заполнен в любом из полей — не перезаписываем
    for field in candidate_fields:
        val = data.get(field)
        if val:
            logger.info("В %s #%s уже заполнен промокод (%s=%s). Пропуск.", entity_type, entity_id, field, val)
            return {
                "ok": True,
                "status": "already_set",
                "entity_id": entity_id,
                "entity_type": entity_type,
                "promo_code": val
            }

    # 3. Ищем текст для извлечения промокода
    promo_code = None

    # А. Из параметров вебхука
    if text:
        promo_code = extract_promo_from_text(text)

    # Б. Из комментариев / описания
    if not promo_code:
        comments = data.get('COMMENTS') or data.get('ADDITIONAL_INFO')
        if comments:
            promo_code = extract_promo_from_text(comments)

    # В. Из таймлайна Wazzup (crm.timeline.comment — именно туда Wazzup пишет сообщения)
    if not promo_code:
        timeline = _b24_call('crm.timeline.comment.list', {
            'filter': {'ENTITY_TYPE': entity_type, 'ENTITY_ID': entity_id},
            'order': {'ID': 'ASC'}
        })
        if timeline and 'result' in timeline:
            for comment in timeline['result']:
                desc = comment.get('COMMENT')
                promo_code = extract_promo_from_text(desc)
                if promo_code:
                    break

    # Г. Из crm.activity (запасной вариант)
    if not promo_code:
        activities = _b24_call('crm.activity.list', {
            'filter': {'OWNER_TYPE_ID': owner_type_id, 'OWNER_ID': entity_id},
            'order': {'ID': 'ASC'}
        })
        if activities and 'result' in activities:
            for act in activities['result']:
                desc = act.get('DESCRIPTION') or act.get('SUBJECT')
                promo_code = extract_promo_from_text(desc)
                if promo_code:
                    break

    # 4. Если промокод найден — записываем во все доступные поля промокода
    if promo_code:
        fields_to_update = {}
        for f in candidate_fields:
            if f in data:
                fields_to_update[f] = promo_code

        if not fields_to_update:
            fields_to_update['UF_CRM_1786105060756'] = promo_code

        update_res = _b24_call(update_method, {
            'id': entity_id,
            'fields': fields_to_update,
            'params': {'REGISTER_SONET_EVENT': 'N'}
        })

        if update_res and update_res.get('result'):
            logger.info("Успешно сохранён промокод '%s' (поля: %s) для %s #%s", promo_code, list(fields_to_update.keys()), entity_type, entity_id)
            return {
                "ok": True,
                "status": "updated",
                "entity_id": entity_id,
                "entity_type": entity_type,
                "promo_code": promo_code,
                "fields": list(fields_to_update.keys())
            }
        else:
            logger.error("Ошибка при записи промокода в %s #%s: %s", entity_type, entity_id, update_res)
            return {"ok": False, "error": f"Failed to update {entity_type} #{entity_id}"}

    logger.info("В %s #%s промокод из 4-8 цифр не обнаружен.", entity_type, entity_id)
    return {
        "ok": True,
        "status": "no_promo_found",
        "entity_id": entity_id,
        "entity_type": entity_type
    }


def extract_and_save_promo_for_deal(deal_id: int | str, text: str | None = None) -> dict:
    return extract_and_save_promo(entity_id=deal_id, entity_type='deal', text=text)


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

