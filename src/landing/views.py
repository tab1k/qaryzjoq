from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import LeadForm


def index(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка принята — юрист свяжется с вами в течение 15 минут.')
            return redirect(reverse('landing:index') + '#contact')
    else:
        form = LeadForm()

    return render(request, 'landing/index.html', {'form': form})
