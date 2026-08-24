from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'debt', 'calc_result', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'message')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('name', 'phone', 'debt', 'message', 'status', 'created_at')}),
        ('Расчёт с калькулятора', {'fields': ('calc_debt', 'calc_payments', 'calc_income', 'calc_result')}),
    )
