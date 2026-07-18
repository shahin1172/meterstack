from .views import DataAPIView
from django.urls import path
from .views import (
    DataAPIView,
    UsageListAPIView,
)
urlpatterns = [
    path(
        "data/",
        DataAPIView.as_view(),
        name="data-endpoint",
    ),
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
]
