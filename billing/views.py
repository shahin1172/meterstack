from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsTenantAdmin

from .filters import InvoiceFilter
from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceListView(ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [
        IsAuthenticated,
        IsTenantAdmin,
    ]

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]

    filterset_class = InvoiceFilter

    ordering_fields = [
        "period",
        "total",
    ]

    ordering = [
        "-period",
    ]

    def get_queryset(self):
        return (
            Invoice.objects
            .filter(
                tenant=self.request.user.tenant,
            )
            .order_by("-period")
        )