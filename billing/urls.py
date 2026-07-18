from django.urls import path

from .views import InvoiceListView

urlpatterns = [
    path(
        "invoices/",
        InvoiceListView.as_view(),
        name="invoice-list",
    ),
]