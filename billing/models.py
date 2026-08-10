from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from tenants.models import Tenant
from usage.models import Endpoint


class PricingPlan(models.Model):
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="pricing_plan",
    )
    flat_monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    included_requests = models.PositiveIntegerField(default=0)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.slug} Pricing Plan"


class Invoice(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    period = models.DateField()
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "period"],
                name="unique_invoice_per_tenant_period",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="invoice_total_non_negative",
            ),
            # New: ensure period is always the first day of a month
            models.CheckConstraint(
                condition=models.Q(period__day=1),
                name="invoice_period_must_be_first_of_month",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "period"]),
        ]
        ordering = ["-period"]

    def __str__(self):
        return f"{self.tenant.slug} - {self.period}"


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    endpoint = models.ForeignKey(
        Endpoint,
        on_delete=models.PROTECT,
    )
    calls = models.PositiveIntegerField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def __str__(self):
        return f"{self.invoice} - {self.endpoint.name}"


class UsageAlert(models.Model):
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="usage_alert",
    )
    monthly_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    threshold_percent = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.slug} Budget Alert"
