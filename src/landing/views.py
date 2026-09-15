from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

from .bitrix24 import extract_and_save_promo_for_deal, send_lead_to_bitrix24
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

    Принимает deal_id (ID сделки) и опциональный текст сообщения.
    Извлекает 4-8 значный промокод и сохраняет в поле сделки.
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

    # Поддерживаем различные форматы передачи ID сделки из роботов Б24
    deal_id = (
        params.get('deal_id')
        or params.get('DEAL_ID')
        or params.get('id')
        or params.get('ID')
        or params.get('document_id')
        or params.get('DOCUMENT_ID')
    )

    # Если передан массив вида ['DEAL', '123']
    if isinstance(deal_id, (list, tuple)):
        deal_id = deal_id[-1]
    elif isinstance(deal_id, str) and '_' in deal_id:
        # Например DEAL_123 -> 123
        deal_id = deal_id.split('_')[-1]

    text = (
        params.get('text')
        or params.get('TEXT')
        or params.get('comment')
        or params.get('COMMENTS')
        or params.get('message')
    )

    if not deal_id:
        return JsonResponse({
            'ok': False,
            'error': 'Missing deal_id parameter (e.g. ?deal_id={{ID}})'
        }, status=400)

    result = extract_and_save_promo_for_deal(deal_id=deal_id, text=text)
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
