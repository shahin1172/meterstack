import django_filters

from .models import UsageRecord


class UsageRecordFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name="user__id")
    endpoint = django_filters.NumberFilter(field_name="endpoint__id")

    start_date = django_filters.DateTimeFilter(
        field_name="timestamp",
        lookup_expr="gte",
    )

    end_date = django_filters.DateTimeFilter(
        field_name="timestamp",
        lookup_expr="lte",
    )

    class Meta:
        model = UsageRecord
        fields = [
            "user",
            "endpoint",
            "start_date",
            "end_date",
        ]