from django.test import TestCase
from __future__ import annotations
from typing import Any
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
import jwt

UserModel = get_user_model()


# ---------------------------------------------------------------------
# Helper: a dummy view that returns a fake object for permission testing
# ---------------------------------------------------------------------
class DummyModel:  # acts like a single object with a tenant attribute
    def __init__(self, tenant: Tenant) -> None:
        self.tenant = tenant


class DummyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsInSameTenant]

    def get(self, request: Any, tenant_slug: str) -> Response:
        # We'll look up the tenant by slug and create a dummy object
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        obj = DummyModel(tenant)
        # Simulate the permission check that DRF does automatically
        self.check_object_permissions(request, obj)
        return Response({"detail": "allowed"})


urlpatterns = [
    path("api/dummy/<slug:tenant_slug>/", DummyDetailView.as_view(), name="dummy-detail"),
]


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------
class AuthenticationTests(APITestCase):
    """Tests for JWT token obtain, refresh, and custom claims."""

    def setUp(self) -> None:
        # Create a tenant and two users (admin and member)
        self.tenant = Tenant.objects.create(
            name="TestCo", slug="testco", api_key="key-12345"
        )
        self.admin_user = User.objects.create_user(
            email="admin@testco.com",
            password="AdminPass1!",
            tenant=self.tenant,
            role="admin",
        )
        self.member_user = User.objects.create_user(
            email="member@testco.com",
            password="MemberPass1!",
            tenant=self.tenant,
            role="member",
        )
        self.client = APIClient()

    def test_token_contains_custom_claims(self) -> None:
        """Obtain token and verify tenant_slug and role are in the payload."""
        response = self.client.post(
            "/api/token/",
            {"email": "admin@testco.com", "password": "AdminPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data["access"]
        # Decode the token (we can use simplejwt functions or just peek manually with base64)



        payload = jwt.decode(access_token, options={"verify_signature": False})
        self.assertIn("tenant_slug", payload)
        self.assertEqual(payload["tenant_slug"], "testco")
        self.assertIn("role", payload)
        self.assertEqual(payload["role"], "admin")

    def test_token_obtain_and_refresh(self) -> None:
        """Obtain token and then refresh it successfully."""
        # Obtain
        response = self.client.post(
            "/api/token/",
            {"email": "admin@testco.com", "password": "AdminPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]

        # Refresh
        refresh_response = self.client.post(
            "/api/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_invalid_credentials(self) -> None:
        """Ensure bad credentials return 401."""
        response = self.client.post(
            "/api/token/",
            {"email": "admin@testco.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token(self) -> None:
        """Refresh with a bad token returns 401."""
        response = self.client.post(
            "/api/token/refresh/",
            {"refresh": "thisisnotarealtoken"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantIsolationTests(APITestCase):
    """Tests that users can only access objects belonging to their own tenant."""

    @override_settings(ROOT_URLCONF=__name__)  # use our dummy URLs
    def setUp(self) -> None:
        self.tenant_a = Tenant.objects.create(
            name="Tenant A", slug="tenant-a", api_key="key-a"
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant B", slug="tenant-b", api_key="key-b"
        )
        self.user_a = User.objects.create_user(
            email="user@a.com",
            password="Pass123!",
            tenant=self.tenant_a,
            role="member",
        )
        self.user_b = User.objects.create_user(
            email="user@b.com",
            password="Pass123!",
            tenant=self.tenant_b,
            role="member",
        )
        self.client = APIClient()

    def _obtain_token(self, email: str, password: str) -> str:
        resp = self.client.post(
            "/api/token/", {"email": email, "password": password}, format="json"
        )
        return resp.data["access"]

    def test_access_own_tenant_object(self) -> None:
        """User A can access an object belonging to tenant A."""
        token = self._obtain_token("user@a.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/dummy/tenant-a/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_access_other_tenant_object(self) -> None:
        """User A cannot access an object belonging to tenant B (403)."""
        token = self._obtain_token("user@a.com", "Pass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/dummy/tenant-b/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_tenant_in_token_fails(self) -> None:
        """If token has no tenant_slug (shouldn't happen), permission denies."""
        # We create a raw token without tenant_slug manually (only for testing)
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user_a)
        del token["tenant_slug"]  # remove custom claim
        # The IsInSameTenant should still work because it reads request.user.tenant,
        # not the token directly. But if the authentication class extracts from token,
        # it would fail. Since our authentication is not yet custom, this test is
        # not meaningful yet. We'll skip for now or note that it's for later.
        pass  # placeholder for future authentication class test

# Create your tests here.
