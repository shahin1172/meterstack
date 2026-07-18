import logging
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['tenant_slug'] = user.tenant.slug   # assumes user has a FK to Tenant with slug
        token['role'] = user.role                  # user.role (admin or member)
        return token

class LoggingTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer   # important! hook our serializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username', 'unknown')
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                logger.info(f"Login successful for user: {username}")
            return response
        except Exception as e:
            logger.warning(f"Failed login attempt for user '{username}': {str(e)}")
            raise

class LoggingTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                logger.info("Token refreshed successfully.")
            return response
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise