from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import LeadForm


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def index(request):
    form = LeadForm()

    if request.method == 'POST':
        submitted = LeadForm(request.POST)

        if submitted.is_valid():
            submitted.save()

            if _is_ajax(request):
                return JsonResponse({'ok': True})

            messages.success(request, 'Спасибо! В рабочее время с вами свяжется наш специалист.')
            return redirect(reverse('landing:index'))

        if _is_ajax(request):
            return JsonResponse({'ok': False, 'errors': submitted.errors}, status=400)

        form = submitted

    return render(request, 'landing/index.html', {
        'form': form,
        'modal_form': LeadForm(auto_id='m_%s'),
    })
