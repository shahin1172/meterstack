from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import Tenant
from users.permissions import IsInSameTenant


class DummyModel:
    """A simple object that carries a tenant for permission testing."""
    def __init__(self, tenant: Tenant) -> None:
        self.tenant = tenant


class DummyDetailView(APIView):
    """Dummy view that checks object-level permissions and returns 200/403."""
    permission_classes = [IsAuthenticated, IsInSameTenant]

    def get(self, request, tenant_slug: str) -> Response:
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj = DummyModel(tenant)
        self.check_object_permissions(request, obj)
        return Response({"detail": "allowed"})