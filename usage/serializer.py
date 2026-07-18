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