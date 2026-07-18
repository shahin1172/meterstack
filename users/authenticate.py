# prac-authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from tenants.models import Tenant

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Step 1: get the user from the token (standard JWT check)
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result

        # Step 2: get the tenant slug from the token claims
        tenant_slug = validated_token.get('tenant_slug')
        if not tenant_slug:
            raise AuthenticationFailed('Token does not contain a tenant slug')

        # Step 3: verify the tenant exists and is active
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            raise AuthenticationFailed('Tenant not found or inactive')

        # Step 4: attach the tenant to the request for later use
        request.tenant = tenant
        return (user, validated_token)