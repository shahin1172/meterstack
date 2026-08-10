from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from tenants.models import Tenant
from usage.models import Endpoint, UsageRecord, UsageSummary
from users.models import User


class DataAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Acme", slug="acme")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@acme.com",
            password="testpass123",
            tenant=self.tenant,
            role="member",
        )
        self.endpoint = Endpoint.objects.create(
            tenant=self.tenant,
            name="Weather",
            path="/weather/",
            price_per_call=Decimal("0.01"),
            price_per_kb=Decimal("0.001"),
        )
        # Obtain token
        token_resp = self.client.post(
            "/api/v1/token/",
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.token = token_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_data_endpoint_records_usage(self):
        response = self.client.post(
            "/api/v1/data/",
            {"endpoint_path": "/weather/"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

        # Verify usage record created
        self.assertEqual(UsageRecord.objects.count(), 1)
        record = UsageRecord.objects.first()
        self.assertEqual(record.calls, 1)
        self.assertGreater(record.data_bytes, 0)
        self.assertGreater(record.cost, Decimal("0"))

        # Verify monthly summary updated
        period = record.timestamp.date().replace(day=1)
        summary = UsageSummary.objects.get(
            tenant=self.tenant,
            endpoint=self.endpoint,
            period=period,
        )
        self.assertEqual(summary.total_calls, 1)

    def test_unauthenticated_request(self):
        self.client.credentials()  # remove token
        response = self.client.post(
            "/api/v1/data/",
            {"endpoint_path": "/weather/"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
