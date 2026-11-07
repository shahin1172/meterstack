import logging
from datetime import date
from django.core.management.base import BaseCommand
from tenants.models import Tenant
from billing.tasks import generate_invoice_task      # ← import the TASK

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
            generate_invoice_task.delay(tenant.id, period.isoformat())
            #                     ↑
            #                     send to worker, don't wait

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Queued {tenants.count()} invoices for {period}"
            )
        )