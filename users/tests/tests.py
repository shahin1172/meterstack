from __future__ import annotations
import jwt
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView
from tenants.models import Tenant
from users.models import User
from users.permissions import IsInSameTenant

User = get_user_model()


class AuthenticationTests(APITestCase):
    """Tests for JWT token obtain, refresh, and custom claims."""

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            name="TestCo", slug="testco", api_key="key-12345"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@testco.com",
            password="AdminPass1!",
            tenant=self.tenant,
            role="admin",
        )
        self.member_user = User.objects.create_user(
            username="member",
            email="member@testco.com",
            password="MemberPass1!",
            tenant=self.tenant,
            role="member",
        )
        self.client = APIClient()

    def test_token_contains_custom_claims(self) -> None:
        response = self.client.post(
            "/api/v1/token/",
            {"username": "admin", "password": "AdminPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data["access"]
        payload = jwt.decode(access_token, options={"verify_signature": False})
        self.assertIn("tenant_slug", payload)
        self.assertEqual(payload["tenant_slug"], "testco")
        self.assertIn("role", payload)
        self.assertEqual(payload["role"], "admin")

    def test_token_obtain_and_refresh(self) -> None:
        response = self.client.post(
            "/api/v1/token/",
            {"username": "admin", "password": "AdminPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]

        refresh_response = self.client.post(
            "/api/v1/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_invalid_credentials(self) -> None:
        response = self.client.post(
            "/api/v1/token/",
            {"username": "admin", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token(self) -> None:
        response = self.client.post(
            "/api/v1/token/refresh/",
            {"refresh": "thisisnotarealtoken"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantIsolationTests(APITestCase):
    """Ensure users can only access objects belonging to their own tenant."""

    @override_settings(ROOT_URLCONF="users.tests.urls")
    def setUp(self) -> None:
        self.tenant_a = Tenant.objects.create(
            name="Tenant A", slug="tenant-a", api_key="key-a"
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B", slug="tenant-b", api_key="key-b"
        )
        self.user_a = User.objects.create_user(
            username="usera",
            email="user@a.com",
            password="Pass123!",
            tenant=self.tenant_a,
            role="member",
        )
        self.user_b = User.objects.create_user(
            username="userb",
            email="user@b.com",
            password="Pass123!",
            tenant=self.tenant_b,
            role="member",
        )
        self.client = APIClient()

    def _obtain_token(self, username: str, password: str) -> str:
        resp = self.client.post(
            "/api/v1/token/",
            {"username": username, "password": password},
            format="json",
        )
        return resp.data["access"]

    def test_access_own_tenant_object(self) -> None:
        token = self._obtain_token("usera", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/dummy/tenant-a/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_other_tenant_object(self) -> None:
        token = self._obtain_token("usera", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/dummy/tenant-b/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

