from django.contrib import admin

from .models import (
    PricingPlan,
    Invoice,
    InvoiceLine,
    UsageAlert,
)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = ('endpoint', 'calls', 'amount')
    can_delete = False
    show_change_link = True


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = (
        'tenant',
        'flat_monthly_fee',
        'discount_percent',
        'included_requests',
        'created_at',
    )
    search_fields = ('tenant__name',)
    raw_id_fields = ('tenant',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'tenant',
        'period',
        'subtotal',
        'discount',
        'total',
        'created_at',
    )
    list_filter = ('period', 'tenant')
    search_fields = ('tenant__name',)
    ordering = ('-period',)
    date_hierarchy = 'period'
    raw_id_fields = ('tenant',)
    inlines = [InvoiceLineInline]


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'endpoint', 'calls', 'amount')
    search_fields = ('invoice__tenant__name', 'endpoint__name')
    raw_id_fields = ('invoice', 'endpoint')


@admin.register(UsageAlert)
class UsageAlertAdmin(admin.ModelAdmin):
    list_display = (
        'tenant',
        'monthly_budget',
        'threshold_percent',
        'is_enabled',
        'created_at',
    )
    list_filter = ('is_enabled',)
    search_fields = ('tenant__name',)
    raw_id_fields = ('tenant',)