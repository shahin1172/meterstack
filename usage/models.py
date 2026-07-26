from django.conf import settings
from django.db import models
from tenants.models import Tenant
from .managers import (
    UsageRecordManager,
    UsageSummaryManager,
)


class Endpoint(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="endpoints",
        db_index=True,
    )

    name = models.CharField(max_length=200)

    path = models.CharField(max_length=500)

    price_per_call = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
    )

    price_per_kb = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "path"],
                name="unique_endpoint_per_tenant",
            ),
        ]

        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["tenant", "path"]),
        ]

        ordering = ["name"]

    def __str__(self):
        return f"{self.tenant.slug} - {self.name}"


class UsageRecord(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="usage_records",
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_records",
    )

    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_records",
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    calls = models.PositiveIntegerField(default=1)

    data_bytes = models.PositiveBigIntegerField(default=0)

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
    )

    # Custom manager
    objects = UsageRecordManager()

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "timestamp"]),
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["tenant", "endpoint"]),
            models.Index(fields=["tenant", "timestamp", "endpoint"]),
        ]

        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.tenant.slug} | "
            f"{self.user} | "
            f"{self.endpoint} | "
            f"{self.timestamp}"
        )


class UsageSummary(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="usage_summaries",
    )

    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.CASCADE,
        related_name="usage_summaries",
    )

    period = models.DateField()

    total_calls = models.PositiveIntegerField(default=0)

    total_bytes = models.PositiveBigIntegerField(default=0)

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        default=0,
    )

    # Custom manager
    objects = UsageSummaryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tenant",
                    "endpoint",
                    "period",
                ],
                name="unique_usage_summary_per_period",
            ),
        ]

        indexes = [
            models.Index(fields=["tenant", "period"]),
            models.Index(fields=["tenant", "endpoint"]),
        ]

        ordering = ["-period"]

    def __str__(self):
        return (
            f"{self.tenant.slug} - "
            f"{self.endpoint.name} - "
            f"{self.period}"
        )