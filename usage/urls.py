from django.urls import path

from .views import (
    DataAPIView,
    UsageListAPIView,
    DashboardSummaryAPIView,
    DashboardTrendsAPIView,
)

urlpatterns = [
    path(
        "data/",
        DataAPIView.as_view(),
        name="data-endpoint",
    ),

    path(
        "usage/",
        UsageListAPIView.as_view(),
        name="usage-list",
    ),

    path(
        "dashboard/summary/",
        DashboardSummaryAPIView.as_view(),
        name="dashboard-summary",
    ),

    path(
        "dashboard/trends/",
        DashboardTrendsAPIView.as_view(),
        name="dashboard-trends",
    ),
]