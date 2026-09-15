from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

from .bitrix24 import extract_and_save_promo, send_lead_to_bitrix24
from .forms import LeadForm


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def index(request):
    form = LeadForm()

    if request.method == 'POST':
        submitted = LeadForm(request.POST)

        if submitted.is_valid():
            lead = submitted.save()
            send_lead_to_bitrix24(lead)

            if _is_ajax(request):
                return JsonResponse({'ok': True, 'redirect_url': reverse('landing:thanks')})

            return redirect(reverse('landing:thanks'))

        if _is_ajax(request):
            return JsonResponse({'ok': False, 'errors': submitted.errors}, status=400)

        form = submitted

    return render(request, 'landing/index.html', {
        'form': form,
        'modal_form': LeadForm(auto_id='m_%s'),
    })


def thanks(request):
    return render(request, 'landing/thanks.html')


@csrf_exempt
def extract_promo_webhook(request):
    """Вебхук для робота Битрикс24 / Wazzup.

    Принимает id (ID лида или сделки) и опциональный текст сообщения.
    Извлекает 4-8 значный промокод и сохраняет в поле карточки.
    """
    params = {}
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                params = json.loads(request.body.decode('utf-8'))
            except Exception:
                params = {}
        else:
            params = request.POST.dict()
    else:
        params = request.GET.dict()

    raw_id = (
        params.get('lead_id')
        or params.get('LEAD_ID')
        or params.get('deal_id')
        or params.get('DEAL_ID')
        or params.get('id')
        or params.get('ID')
        or params.get('document_id')
        or params.get('DOCUMENT_ID')
    )

    entity_type = 'lead'
    if 'deal_id' in params or 'DEAL_ID' in params:
        entity_type = 'deal'
    elif 'lead_id' in params or 'LEAD_ID' in params:
        entity_type = 'lead'

    entity_id = raw_id
    if isinstance(raw_id, (list, tuple)):
        raw_id_str = str(raw_id[-1])
        if 'DEAL' in str(raw_id[0]):
            entity_type = 'deal'
        elif 'LEAD' in str(raw_id[0]):
            entity_type = 'lead'
        entity_id = raw_id_str
    elif isinstance(raw_id, str):
        if raw_id.startswith('DEAL_'):
            entity_type = 'deal'
            entity_id = raw_id.replace('DEAL_', '')
        elif raw_id.startswith('LEAD_'):
            entity_type = 'lead'
            entity_id = raw_id.replace('LEAD_', '')

    text = (
        params.get('text')
        or params.get('TEXT')
        or params.get('comment')
        or params.get('COMMENTS')
        or params.get('message')
    )

    if not entity_id:
        return JsonResponse({
            'ok': False,
            'error': 'Missing id parameter (e.g. ?id={{ID}})'
        }, status=400)

    result = extract_and_save_promo(entity_id=entity_id, entity_type=entity_type, text=text)
    return JsonResponse(result)


def robots_txt(request):
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    content = f"""User-agent: *
Allow: /
Disallow: /admin/

Sitemap: {scheme}://{host}/sitemap.xml
"""
    return HttpResponse(content.strip(), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{scheme}://{host}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return HttpResponse(content.strip(), content_type="application/xml; charset=utf-8")
