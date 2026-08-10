from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.settings import api_settings

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Override to always select the tenant when fetching the user.
        This eliminates an extra query later.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise AuthenticationFailed('Token contained no recognizable user identification')

        try:
            user = User.objects.select_related('tenant').get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

        return user

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result
        tenant_slug = validated_token.get('tenant_slug')
        if not tenant_slug:
            raise AuthenticationFailed('Token does not contain a tenant slug')

        # Tenant already preloaded via select_related, so request.user.tenant is cached
        return (user, validated_token)