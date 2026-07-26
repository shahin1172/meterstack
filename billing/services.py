from decimal import Decimal
from django.db import transaction
from usage.models import UsageSummary
from .models import PricingPlan, Invoice, InvoiceLine
import logging
from decimal import Decimal
from .models import UsageAlert

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

    logger = logging.getLogger(__name__)

    @staticmethod
    def check_budget_alert(*, invoice):

        try:
            alert = UsageAlert.objects.get(
                tenant=invoice.tenant,
                is_enabled=True,
            )

        except UsageAlert.DoesNotExist:
            return

        threshold_amount = (
                alert.monthly_budget *
                Decimal(alert.threshold_percent) /
                Decimal("100")
        )

        if invoice.total >= threshold_amount:
            logger.warning(
                "Budget alert | tenant=%s invoice_total=%s budget=%s threshold=%s%%",
                invoice.tenant.slug,
                invoice.total,
                alert.monthly_budget,
                alert.threshold_percent,
            )