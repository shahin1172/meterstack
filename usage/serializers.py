from rest_framework import serializers
from rest_framework import serializers
from .models import UsageRecord



class DataRequestSerializer(serializers.Serializer):
    endpoint_path = serializers.CharField(max_length=500)




class UsageRecordSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    endpoint_name = serializers.CharField(
        source="endpoint.name",
        read_only=True,
    )

    class Meta:
        model = UsageRecord
        fields = [
            "id",
            "user_email",
            "endpoint_name",
            "timestamp",
            "calls",
            "data_bytes",
            "cost",
        ]


from rest_framework import serializers


class TopEndpointSerializer(serializers.Serializer):
    endpoint__name = serializers.CharField()

    total_calls = serializers.IntegerField()

    total_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
    )


class PeriodSummarySerializer(serializers.Serializer):
    total_calls = serializers.IntegerField()

    total_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
    )

    total_bytes = serializers.IntegerField()


class PeriodComparisonSerializer(serializers.Serializer):
    current = PeriodSummarySerializer()

    previous = PeriodSummarySerializer()


class DashboardSummarySerializer(serializers.Serializer):
    top_endpoints = TopEndpointSerializer(
        many=True,
    )

    comparison = PeriodComparisonSerializer()


class DailyTrendSerializer(serializers.Serializer):
    day = serializers.DateField()

    total_calls = serializers.IntegerField()

    total_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
    )


class DashboardTrendSerializer(serializers.Serializer):
    trends = DailyTrendSerializer(
        many=True,
    )