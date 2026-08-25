"""Данные для главной страницы админки."""

from django.db.models import Count, Q, Sum
from django.urls import reverse

from .models import Lead


def dashboard_callback(request, context):
    stats = Lead.objects.aggregate(
        total=Count('id'),
        new=Count('id', filter=Q(status=Lead.Status.NEW)),
        in_work=Count('id', filter=Q(status=Lead.Status.IN_WORK)),
        done=Count('id', filter=Q(status=Lead.Status.DONE)),
        with_calc=Count('id', filter=Q(calc_debt__isnull=False)),
        debt_sum=Sum('calc_debt'),
    )

    link = reverse('admin:landing_lead_changelist')

    context.update({
        'cards': [
            {'title': 'Всего заявок', 'value': stats['total'], 'link': link, 'icon': 'inbox'},
            {'title': 'Новые', 'value': stats['new'], 'link': f'{link}?status__exact={Lead.Status.NEW}', 'icon': 'mark_email_unread'},
            {'title': 'В работе', 'value': stats['in_work'], 'link': f'{link}?status__exact={Lead.Status.IN_WORK}', 'icon': 'pending_actions'},
            {'title': 'Обработано', 'value': stats['done'], 'link': f'{link}?status__exact={Lead.Status.DONE}', 'icon': 'task_alt'},
        ],
        'calc_stats': {
            'with_calc': stats['with_calc'],
            'debt_sum': stats['debt_sum'] or 0,
        },
        'recent_leads': Lead.objects.order_by('-created_at')[:8],
    })

    return context
