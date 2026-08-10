from django.test import TestCase
from datetime import date
from decimal import Decimal
from django.test import TestCase
from billing.models import PricingPlan, Invoice
from .services import BillingService
from tenants.models import Tenant
from usage.models import Endpoint, UsageSummary
from datetime import date
from decimal import Decimal
from django.test import TestCase
from billing.models import UsageAlert
from billing.services import BillingService
from datetime import date
from django.core.management import call_command
from django.test import TestCase
from .models import Invoice


class BillingServiceTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme")

        self.endpoint = Endpoint.objects.create(
            tenant=self.tenant,
            name="Weather API",
            path="/weather/",
            price_per_call=Decimal("0.05"),
        )

        PricingPlan.objects.create(
            tenant=self.tenant,
            flat_monthly_fee=Decimal("10.00"),
            discount_percent=Decimal("10.00"),
        )

        UsageSummary.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint,
            period=date(2026, 3, 1),
            total_calls=100,
            total_cost=Decimal("50.00"),
        )

    def test_generate_invoice(self):

        invoice = BillingService.generate_invoice(
            tenant=self.tenant,
            period=date(2026, 3, 1),
        )

        self.assertEqual(invoice.subtotal, Decimal("60.00"))
        self.assertEqual(invoice.discount, Decimal("6.00"))
        self.assertEqual(invoice.total, Decimal("54.00"))

        self.assertEqual(Invoice.objects.count(), 1)




class BillingCommandTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme")
        self.endpoint = Endpoint.objects.create(
            tenant=self.tenant,
            name="Weather API",
            path="/weather/",
            price_per_call=Decimal("0.05"),
        )
        PricingPlan.objects.create(
            tenant=self.tenant,
            flat_monthly_fee=Decimal("10.00"),
            discount_percent=Decimal("10.00"),
        )
        UsageSummary.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint,
            period=date(2026, 3, 1),
            total_calls=100,
            total_cost=Decimal("50.00"),
        )

    def test_command_does_not_create_duplicate_invoice(self):
        call_command("generate_invoices", period="2026-03-01")
        call_command("generate_invoices", period="2026-03-01")

        self.assertEqual(Invoice.objects.count(), 1)




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


# Create your tests here.
