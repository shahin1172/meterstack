import django_filters

from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="period",
        lookup_expr="gte",
    )

    end_date = django_filters.DateFilter(
        field_name="period",
        lookup_expr="lte",
    )

    class Meta:
        model = Invoice
        fields = [
            "start_date",
            "end_date",
        ]