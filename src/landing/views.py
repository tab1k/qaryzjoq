from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .bitrix24 import send_lead_to_bitrix24
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
