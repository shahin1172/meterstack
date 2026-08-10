from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from django.db import transaction

from tenants.models import Tenant
from usage.models import UsageSummary
from .models import Invoice, InvoiceLine, PricingPlan, UsageAlert

logger = logging.getLogger(__name__)


class BillingService:
    @staticmethod
    @transaction.atomic
    def generate_invoice(*, tenant: Tenant, period: date) -> Invoice:

        period = period.replace(day=1)

        summaries = (
            UsageSummary.objects
            .select_for_update()
            .filter(tenant=tenant, period=period)
        )

        if Invoice.objects.filter(tenant=tenant, period=period).exists():
            raise ValueError("Invoice already exists.")

        pricing = PricingPlan.objects.get(tenant=tenant)
        usage_cost = sum((summary.total_cost for summary in summaries), Decimal("0.00"))
        subtotal = pricing.flat_monthly_fee + usage_cost
        discount = subtotal * pricing.discount_percent / Decimal("100")
        total = subtotal - discount

        invoice = Invoice.objects.create(
            tenant=tenant,
            period=period,
            subtotal=subtotal,
            discount=discount,
            total=total,
        )


        lines = [
            InvoiceLine(
                invoice=invoice,
                endpoint=summary.endpoint,
                calls=summary.total_calls,
                amount=summary.total_cost,
            )
            for summary in summaries
        ]
        InvoiceLine.objects.bulk_create(lines)

        return invoice

    @staticmethod
    def check_budget_alert(*, invoice: Invoice) -> None:
        try:
            alert = UsageAlert.objects.get(
                tenant=invoice.tenant, is_enabled=True
            )
        except UsageAlert.DoesNotExist:
            return

        threshold_amount = (
            alert.monthly_budget
            * Decimal(alert.threshold_percent)
            / Decimal("100")
        )
        if invoice.total >= threshold_amount:
            logger.warning(
                "Budget alert | tenant=%s invoice_total=%s budget=%s threshold=%s%%",
                invoice.tenant.slug,
                invoice.total,
                alert.monthly_budget,
                alert.threshold_percent,
            )
