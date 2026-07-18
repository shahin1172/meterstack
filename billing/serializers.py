from rest_framework import serializers

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id",
            "period",
            "subtotal",
            "discount",
            "total",
            "created_at",
        ]