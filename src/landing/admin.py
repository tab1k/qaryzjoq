from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter
from unfold.decorators import action, display

from .models import Lead


def money(value):
    if value is None:
        return '—'
    return f'{value:,}'.replace(',', ' ') + ' ₸'


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ('created_short', 'name', 'phone_link', 'calc_short', 'status_badge')
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateFilter),
    )
    list_filter_submit = True
    search_fields = ('name', 'phone', 'message', 'debt')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 30

    readonly_fields = ('created_at', 'calc_card')
    actions = ('mark_in_work', 'mark_done')

    fieldsets = (
        ('Заявка', {
            'fields': ('name', 'phone', 'status', 'created_at'),
        }),
        ('Что написал клиент', {
            'fields': ('debt', 'message'),
            'classes': ('collapse',),
        }),
        ('Расчёт с калькулятора', {
            'fields': ('calc_card', 'calc_debt', 'calc_payments', 'calc_income', 'calc_result'),
        }),
    )

    # --- колонки списка ---------------------------------------------------

    @display(description='Дата', ordering='created_at')
    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    @display(description='Телефон')
    def phone_link(self, obj):
        digits = ''.join(ch for ch in obj.phone if ch.isdigit())
        return format_html(
            '<a href="tel:+{0}" style="font-weight:600">{1}</a> '
            '<a href="https://wa.me/{0}" target="_blank" '
            'style="margin-left:6px;color:#25D366;font-weight:600">WhatsApp</a>',
            digits, obj.phone,
        )

    @display(description='Расчёт')
    def calc_short(self, obj):
        if not obj.has_calc:
            return format_html('<span style="opacity:.5">{}</span>', 'без расчёта')
        return format_html(
            '<b>{}</b> в месяц<br><span style="opacity:.6">долг {}</span>',
            money(obj.calc_result), money(obj.calc_debt),
        )

    @display(
        description='Статус',
        ordering='status',
        label={
            Lead.Status.NEW: 'danger',
            Lead.Status.IN_WORK: 'warning',
            Lead.Status.DONE: 'success',
        },
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    # --- карточка расчёта в форме ------------------------------------------

    @display(description='Итог расчёта')
    def calc_card(self, obj):
        if not obj.has_calc:
            return 'Клиент оставил заявку без расчёта на калькуляторе.'

        rows = [
            ('Сумма кредитов', money(obj.calc_debt)),
            ('Платит сейчас в месяц', money(obj.calc_payments)),
            ('Официальный доход', money(obj.calc_income)),
            ('Новый платёж', money(obj.calc_result)),
        ]
        cells = format_html_join(
            '',
            '<div style="padding:10px 14px;border-radius:10px;background:#ecf7f0">'
            '<div style="font-size:11px;opacity:.7">{}</div>'
            '<div style="font-size:16px;font-weight:700;color:#046c35">{}</div></div>',
            rows,
        )
        return format_html(
            '<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));'
            'gap:10px;max-width:520px">{}</div>',
            cells,
        )

    # --- массовые действия -------------------------------------------------

    @action(description='Перевести в «В работе»', icon='play_arrow')
    def mark_in_work(self, request, queryset):
        updated = queryset.update(status=Lead.Status.IN_WORK)
        self.message_user(request, f'В работу переведено заявок: {updated}', messages.SUCCESS)

    @action(description='Отметить обработанными', icon='check')
    def mark_done(self, request, queryset):
        updated = queryset.update(status=Lead.Status.DONE)
        self.message_user(request, f'Обработано заявок: {updated}', messages.SUCCESS)


# --- пользователи и группы в общем стиле темы -------------------------------

from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class StyledUserAdmin(UserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class StyledGroupAdmin(GroupAdmin, ModelAdmin):
    pass
