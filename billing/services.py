from decimal import Decimal

from django.db import transaction

from usage.models import UsageSummary

from .models import PricingPlan, Invoice, InvoiceLine


class BillingService:

    @staticmethod
    @transaction.atomic
    def generate_invoice(*, tenant, period):

        summaries = (
            UsageSummary.objects
            .select_for_update()
            .filter(
                tenant=tenant,
                period=period,
            )
        )

        if Invoice.objects.filter(
            tenant=tenant,
            period=period,
        ).exists():
            raise ValueError("Invoice already exists.")

        pricing = PricingPlan.objects.get(
            tenant=tenant
        )

        usage_cost = sum(
            summary.total_cost
            for summary in summaries
        )

        subtotal = pricing.flat_monthly_fee + usage_cost

        discount = (
            subtotal *
            pricing.discount_percent /
            Decimal("100")
        )

        total = subtotal - discount

        invoice = Invoice.objects.create(
            tenant=tenant,
            period=period,
            subtotal=subtotal,
            discount=discount,
            total=total,
        )

        for summary in summaries:
            InvoiceLine.objects.create(
                invoice=invoice,
                endpoint=summary.endpoint,
                calls=summary.total_calls,
                amount=summary.total_cost,
            )

        return invoice