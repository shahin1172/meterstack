from datetime import date

from django.core.management import call_command
from django.test import TestCase

from billing.models import Invoice


class BillingCommandTests(TestCase):

    def test_command_does_not_create_duplicate_invoice(self):

        call_command(
            "generate_invoices",
            period="2026-03-01",
        )

        call_command(
            "generate_invoices",
            period="2026-03-01",
        )

        self.assertEqual(
            Invoice.objects.count(),
            1,
        )