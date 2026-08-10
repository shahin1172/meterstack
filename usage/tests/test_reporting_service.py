from datetime import date, timedelta
from decimal import Decimal
from django.core.cache import cache
from django.test import TestCase
from tenants.models import Tenant
from usage.models import Endpoint, UsageRecord, UsageSummary
from usage.services.reporting import ReportingService


class ReportingServiceTests(TestCase):

    def setUp(self):

        cache.clear()

        self.tenant = Tenant.objects.create(
            name="Acme",
            slug="acme",
        )

        self.endpoint1 = Endpoint.objects.create(
            tenant=self.tenant,
            name="Weather",
            path="/weather/",
            price_per_call=Decimal("0.10"),
            price_per_kb=Decimal("0.01"),
        )

        self.endpoint2 = Endpoint.objects.create(
            tenant=self.tenant,
            name="News",
            path="/news/",
            price_per_call=Decimal("0.20"),
            price_per_kb=Decimal("0.02"),
        )

        self.current_period = date.today().replace(day=1)

        self.previous_period = (
            self.current_period - timedelta(days=30)
        ).replace(day=1)

        UsageSummary.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint1,
            period=self.current_period,
            total_calls=500,
            total_bytes=50000,
            total_cost=Decimal("55.50"),
        )

        UsageSummary.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint2,
            period=self.current_period,
            total_calls=200,
            total_bytes=20000,
            total_cost=Decimal("22.20"),
        )

        UsageSummary.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint1,
            period=self.previous_period,
            total_calls=100,
            total_bytes=10000,
            total_cost=Decimal("11.10"),
        )

        UsageRecord.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint1,
            calls=20,
            data_bytes=2000,
            cost=Decimal("2.20"),
        )

        UsageRecord.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint1,
            calls=30,
            data_bytes=3000,
            cost=Decimal("3.30"),
        )

        UsageRecord.objects.create(
            tenant=self.tenant,
            endpoint=self.endpoint2,
            calls=10,
            data_bytes=1000,
            cost=Decimal("1.10"),
        )

        self.top_endpoint_cache_key = (
            f"{ReportingService.CACHE_PREFIX}:"
            f"top_endpoints:"
            f"{self.tenant.slug}:5"
        )

    def test_get_top_endpoints(self):

        result = ReportingService.get_top_endpoints(
            tenant=self.tenant,
        )

        self.assertEqual(
            len(result),
            2,
        )

        self.assertEqual(
            result[0]["endpoint__name"],
            "Weather",
        )

        self.assertEqual(
            result[0]["total_calls"],
            600,
        )

        self.assertEqual(
            result[1]["endpoint__name"],
            "News",
        )

        self.assertEqual(
            result[1]["total_calls"],
            200,
        )

    def test_get_daily_usage_trends(self):

        result = ReportingService.get_daily_usage_trends(
            tenant=self.tenant,
            days=30,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["total_calls"],
            60,
        )

        self.assertEqual(
            result[0]["total_cost"],
            Decimal("6.60"),
        )

    def test_compare_periods(self):

        result = ReportingService.compare_periods(
            tenant=self.tenant,
            current_period=self.current_period,
            previous_period=self.previous_period,
        )

        self.assertEqual(
            result["current"]["total_calls"],
            700,
        )

        self.assertEqual(
            result["previous"]["total_calls"],
            100,
        )

        self.assertEqual(
            result["current"]["total_cost"],
            Decimal("77.70"),
        )

        self.assertEqual(
            result["previous"]["total_cost"],
            Decimal("11.10"),
        )

    def test_dashboard_cache_created(self):

        cache.clear()

        self.assertIsNone(
            cache.get(self.top_endpoint_cache_key),
        )

        ReportingService.get_top_endpoints(
            tenant=self.tenant,
        )

        self.assertIsNotNone(
            cache.get(self.top_endpoint_cache_key),
        )

    def test_dashboard_cache_hit(self):

        cache.clear()

        first_result = ReportingService.get_top_endpoints(
            tenant=self.tenant,
        )

        second_result = ReportingService.get_top_endpoints(
            tenant=self.tenant,
        )

        self.assertEqual(
            first_result,
            second_result,
        )

        self.assertIsNotNone(
            cache.get(self.top_endpoint_cache_key),
        )


    def test_dashboard_cache_invalidated(self):
            cache.clear()
            ReportingService.get_top_endpoints(
                tenant=self.tenant,
            )
            self.assertIsNotNone(
                cache.get(self.top_endpoint_cache_key),
            )

            ReportingService.invalidate_dashboard_cache(
                tenant=self.tenant,
            )
            self.assertIsNone(
                cache.get(self.top_endpoint_cache_key),
            )