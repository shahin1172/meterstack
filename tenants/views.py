import logging
from rest_framework import generics, status
from rest_framework.response import Response
from tenants.serializers import TenantRegistrationSerializer

logger = logging.getLogger(__name__)

class TenantRegistrationView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantRegistrationSerializer

    def create(self, request, *args, **kwargs) -> Response:
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)          # <-- perform_create called here
            tenant_slug = serializer.validated_data.get('slug')
            logger.info(f"Tenant registered successfully: slug={tenant_slug}")
            headers = self.get_success_headers(serializer.data) #exactly where to find the new tenant
            return Response(
                {"message": "Tenant and admin user created successfully."},
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            logger.warning(f"Tenant registration failed: {str(e)}")
            raise