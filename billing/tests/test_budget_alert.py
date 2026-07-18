from datetime import date
from decimal import Decimal

from django.test import TestCase

from billing.models import UsageAlert
from billing.services import BillingService


class BudgetAlertTests(TestCase):

    def test_budget_alert_is_triggered(self):

        UsageAlert.objects.create(
            tenant=self.tenant,
            monthly_budget=Decimal("100.00"),
            threshold_percent=80,
        )

        invoice = BillingService.generate_invoice(
            tenant=self.tenant,
            period=date(2026, 3, 1),
        )

        with self.assertLogs("billing.services") as logs:

            BillingService.check_budget_alert(
                invoice=invoice,
            )

        self.assertIn(
            "Budget alert",
            logs.output[0],
        )