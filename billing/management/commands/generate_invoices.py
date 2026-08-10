import logging
from datetime import date
from django.core.management.base import BaseCommand
from tenants.models import Tenant
from billing.services import BillingService
from billing.models import PricingPlan, Invoice, InvoiceLine, UsageAlert

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate monthly invoices for all active tenants."

    def add_arguments(self, parser):
        parser.add_argument(
            "--period",
            type=str,
            help="Billing period (YYYY-MM-01). Example: 2026-03-01",
        )

    def handle(self, *args, **options):

        period = (
            date.fromisoformat(options["period"])
            if options["period"]
            else date.today().replace(day=1)
        )

        tenants = Tenant.objects.filter(is_active=True)



        for tenant in tenants:
            try:
                invoice=BillingService.generate_invoice(
                    tenant=tenant,
                    period=period,
                )
                BillingService.check_budget_alert(
                    invoice=invoice,
                )


                logger.info(
                    "Invoice generated for tenant '%s'",
                    tenant.slug,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {tenant.slug}"
                    )
                )

            except Exception as exc:

                logger.exception(
                    "Billing failed for tenant '%s'",
                    tenant.slug,
                )

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {tenant.slug}: {exc}"
                    )
                )