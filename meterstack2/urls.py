"""
URL configuration for meterstack2 project.
"""
from django.contrib import admin
from django.urls import path, include
from core.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT token endpoints
    path('api/v1/', include('users.urls')),

    # Tenant registration
    path('api/v1/', include('tenants.urls')),

    # Usage endpoints & dashboards
    path('api/v1/', include('usage.urls')),

    # Billing invoices
    path('api/v1/', include('billing.urls')),

    path('api/health/', HealthCheckView.as_view(), name='health-check'),
]