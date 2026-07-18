# core/prac-authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):

        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result

       tenant_slug = validated_token.get('tenant_slug')

        if tenant_slug is None:

            return (user, validated_token)

        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:

            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('Invalid tenant in token')

        request.tenant = tenant

        return (user, validated_token)

