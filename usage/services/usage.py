import logging
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F, QuerySet
from django.shortcuts import get_object_or_404

from core.decorators import retry_on_deadlock
from tenants.models import Tenant
from usage.models import Endpoint, UsageRecord, UsageSummary

logger = logging.getLogger(__name__)


class UsageService:
    @staticmethod
    def calculate_cost(
        *,
        endpoint: Endpoint,
        calls: int,
        data_bytes: int,
    ) -> Decimal:
        """Calculate the cost of a single usage event."""
        data_kb = Decimal(data_bytes) / Decimal(1024)
        return (
            endpoint.price_per_call * calls
            + endpoint.price_per_kb * data_kb
        )

    @staticmethod
    def get_current_period():
        """Return the first day of the current month (e.g. 2026-07-01)."""
        today = date.today()
        return today.replace(day=1)

    @staticmethod
    def get_data_size(payload: dict) -> int:
        """
        Return the byte size of a payload dictionary as it would be
        transmitted over the wire.
        """
        return len(str(payload).encode("utf-8"))

    @staticmethod
    @retry_on_deadlock()
    @transaction.atomic
    def update_usage_summary(
        *,
        tenant: Tenant,
        endpoint: Endpoint,
        calls: int,
        data_bytes: int,
        cost: Decimal,
    ) -> UsageSummary:
        """
        Thread‑safe update of the monthly usage summary.
        Uses an atomic update-first approach to avoid race conditions.
        """
        period = UsageService.get_current_period()

        # Try to update an existing row
        updated = (
            UsageSummary.objects
            .select_for_update()
            .filter(
                tenant=tenant,
                endpoint=endpoint,
                period=period,
            )
            .update(
                total_calls=F("total_calls") + calls,
                total_bytes=F("total_bytes") + data_bytes,
                total_cost=F("total_cost") + cost,
            )
        )

        if updated == 0:
            # Row didn't exist – create it.
            summary, created = UsageSummary.objects.get_or_create(
                tenant=tenant,
                endpoint=endpoint,
                period=period,
                defaults={
                    "total_calls": calls,
                    "total_bytes": data_bytes,
                    "total_cost": cost,
                },
            )

            if not created:
                # Another thread created it while we were trying;
                # update the row we just fetched with a lock
                summary = (
                    UsageSummary.objects
                    .select_for_update()
                    .get(pk=summary.pk)
                )
                summary.total_calls = F("total_calls") + calls
                summary.total_bytes = F("total_bytes") + data_bytes
                summary.total_cost = F("total_cost") + cost
                summary.save(update_fields=["total_calls", "total_bytes", "total_cost"])

        # Always return the final row
        summary = UsageSummary.objects.get(
            tenant=tenant,
            endpoint=endpoint,
            period=period,
        )
        return summary

    @staticmethod
    def create_usage_record(
        *,
        tenant: Tenant,
        user,
        endpoint: Endpoint,
        calls: int,
        data_bytes: int,
        cost: Decimal,
    ) -> UsageRecord:
        """Store one immutable usage record."""
        return UsageRecord.objects.create(
            tenant=tenant,
            user=user,
            endpoint=endpoint,
            calls=calls,
            data_bytes=data_bytes,
            cost=cost,
        )

    @staticmethod
    def record_usage(
        *,
        tenant: Tenant,
        user,
        endpoint: Endpoint,
        calls: int = 1,
        data_bytes: int = 0,
    ) -> UsageRecord:
        """
        Record one API usage event.

        Workflow:
        1. Calculate cost
        2. Update monthly summary
        3. Create immutable usage record

        (Cache invalidation is now handled by the calling view.)
        """
        cost = UsageService.calculate_cost(
            endpoint=endpoint,
            calls=calls,
            data_bytes=data_bytes,
        )

        UsageService.update_usage_summary(
            tenant=tenant,
            endpoint=endpoint,
            calls=calls,
            data_bytes=data_bytes,
            cost=cost,
        )

        usage_record = UsageService.create_usage_record(
            tenant=tenant,
            user=user,
            endpoint=endpoint,
            calls=calls,
            data_bytes=data_bytes,
            cost=cost,
        )

        logger.info(
            "Usage recorded | tenant=%s endpoint=%s user=%s calls=%s bytes=%s cost=%s",
            tenant.slug,
            endpoint.path,
            getattr(user, "email", None),
            calls,
            data_bytes,
            cost,
        )

        return usage_record

    @staticmethod
    def get_active_endpoint(*, tenant, endpoint_path: str) -> Endpoint:
        """Return an active endpoint for the given tenant."""
        return get_object_or_404(
            Endpoint,
            tenant=tenant,
            path=endpoint_path,
            is_active=True,
        )

    @staticmethod
    def get_filtered_usage(*, tenant) -> QuerySet:
        """
        Base queryset for the usage dashboard.
        Filtering, searching and pagination are handled by DRF backends.
        """
        return (
            UsageRecord.objects
            .filter(tenant=tenant)
            .select_related("user", "endpoint")
            .order_by("-timestamp")
        )