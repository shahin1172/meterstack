from datetime import date
from decimal import Decimal
from django.test import TestCase
from billing.models import PricingPlan, Invoice
from billing.services import BillingService
from tenants.models import Tenant
from usage.models import Endpoint, UsageSummary


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