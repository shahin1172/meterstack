import concurrent.futures
from decimal import Decimal

from django.test import TransactionTestCase
from django.utils import timezone

from tenants.models import Tenant
from users.models import User

from usage.models import Endpoint, UsageRecord, UsageSummary
from usage.services import UsageService


class UsageConcurrencyTests(TransactionTestCase):
    """
    Verify that concurrent requests never lose or double-count usage.
    """

    reset_sequences = True

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(
            name="Acme Inc.",
            slug="acme",
            api_key="test-api-key",
        )

        cls.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="password123",
            tenant=cls.tenant,
            role="member",
        )

        cls.endpoint = Endpoint.objects.create(
            tenant=cls.tenant,
            name="Weather API",
            path="/weather/",
            price_per_call=Decimal("0.01000000"),
            price_per_kb=Decimal("0.00100000"),
        )

    def test_concurrent_usage_recording(self):
        """
        Simulate many users calling the API simultaneously.
        """

        total_requests = 50
        bytes_per_request = 1024

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=20
        ) as executor:

            futures = [
                executor.submit(
                    UsageService.record_usage,
                    tenant=self.tenant,
                    user=self.user,
                    endpoint=self.endpoint,
                    calls=1,
                    data_bytes=bytes_per_request,
                )
                for _ in range(total_requests)
            ]

            for future in futures:
                future.result()

        self.assertEqual(
            UsageRecord.objects.count(),
            total_requests,
        )

        period = timezone.now().date().replace(day=1)

        summary = UsageSummary.objects.get(
            tenant=self.tenant,
            endpoint=self.endpoint,
            period=period,
        )

        self.assertEqual(
            summary.total_calls,
            total_requests,
        )

        self.assertEqual(
            summary.total_bytes,
            total_requests * bytes_per_request,
        )

        expected_cost_per_request = (
            self.endpoint.price_per_call
            + self.endpoint.price_per_kb
            * Decimal(bytes_per_request)
            / Decimal(1024)
        )

        expected_total_cost = (
            expected_cost_per_request * total_requests
        )

        self.assertEqual(
            summary.total_cost,
            expected_total_cost,
        )

    def test_every_usage_record_is_created(self):
        """
        Every request should create exactly one UsageRecord.
        """

        request_count = 25

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=10
        ) as executor:

            futures = [
                executor.submit(
                    UsageService.record_usage,
                    tenant=self.tenant,
                    user=self.user,
                    endpoint=self.endpoint,
                    data_bytes=512,
                )
                for _ in range(request_count)
            ]

            for future in futures:
                future.result()

        records = UsageRecord.objects.filter(
            tenant=self.tenant,
            endpoint=self.endpoint,
        )

        self.assertEqual(records.count(), request_count)

        for record in records:
            self.assertEqual(record.calls, 1)
            self.assertEqual(record.data_bytes, 512)
            self.assertIsNotNone(record.cost)
            self.assertEqual(record.user, self.user)
            self.assertEqual(record.endpoint, self.endpoint)

    def test_only_one_summary_row_is_created(self):
        """
        Concurrent requests should never create duplicate monthly summaries.
        """

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=30
        ) as executor:

            futures = [
                executor.submit(
                    UsageService.record_usage,
                    tenant=self.tenant,
                    user=self.user,
                    endpoint=self.endpoint,
                    data_bytes=100,
                )
                for _ in range(100)
            ]

            for future in futures:
                future.result()

        period = timezone.now().date().replace(day=1)

        self.assertEqual(
            UsageSummary.objects.filter(
                tenant=self.tenant,
                endpoint=self.endpoint,
                period=period,
            ).count(),
            1,
        )

