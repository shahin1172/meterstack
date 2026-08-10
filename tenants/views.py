import logging
from rest_framework import generics, status
from rest_framework.response import Response

from tenants.models import Tenant
from tenants.serializers import TenantRegistrationSerializer

logger = logging.getLogger(__name__)


class TenantRegistrationView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantRegistrationSerializer

    def create(self, request, *args, **kwargs) -> Response:
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            tenant = serializer.save()

            logger.info("Tenant registered successfully: slug=%s", tenant.slug)

            headers = self.get_success_headers(serializer.data)

            return Response(
                {
                    "message": "Tenant and admin user created successfully.",
                    "tenant": {
                        "name": tenant.name,
                        "slug": tenant.slug,
                    },
                },
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except Exception as e:
            logger.warning("Tenant registration failed: %s", str(e))
            raise