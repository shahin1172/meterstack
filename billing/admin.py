from django.contrib import admin
from django.contrib import admin

from .models import PricingPlan


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "name",
        "pricing_type",
        "monthly_fee",
        "discount_percentage",
        "is_active",
    )

    list_filter = (
        "pricing_type",
        "is_active",
    )

    search_fields = (
        "tenant__name",
        "name",
    )

    ordering = (
        "tenant__name",
    )

from django.contrib import admin

from .models import (
    PricingPlan,
    Invoice,
    InvoiceLine,
)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = (
        "endpoint",
        "total_calls",
        "total_bytes",
        "unit_price",
        "amount",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "period",
        "status",
        "total_amount",
        "generated_at",
    )

    list_filter = (
        "status",
        "period",
    )

    search_fields = (
        "tenant__name",
    )

    ordering = (
        "-period",
    )

    inlines = [
        InvoiceLineInline,
    ]


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "endpoint",
        "total_calls",
        "amount",
    )

    search_fields = (
        "invoice__tenant__name",
        "endpoint__name",
    )

# Register your models here.
