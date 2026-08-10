from django.urls import path

from .views import DummyDetailView

urlpatterns = [
    path(
        "api/dummy/<slug:tenant_slug>/",
        DummyDetailView.as_view(),
        name="dummy-detail",
    ),
]