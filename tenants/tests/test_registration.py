from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User


class TenantRegistrationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/tenants/register/"

    def test_register_tenant_creates_tenant_and_admin(self):
        data = {
            "name": "New Corp",
            "slug": "new-corp",
            "admin_username": "admin",
            "admin_email": "admin@newcorp.com",
            "admin_password": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tenant", response.data)
        self.assertEqual(response.data["tenant"]["slug"], "new-corp")

        self.assertTrue(Tenant.objects.filter(slug="new-corp").exists())
        admin = User.objects.get(email="admin@newcorp.com")
        self.assertEqual(admin.role, "admin")
        self.assertEqual(admin.tenant.slug, "new-corp")
