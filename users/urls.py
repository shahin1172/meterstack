from django.urls import path
from .token import LoggingTokenObtainPairView, LoggingTokenRefreshView

urlpatterns = [
    path('token/', LoggingTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', LoggingTokenRefreshView.as_view(), name='token_refresh'),
]