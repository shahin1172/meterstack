import logging
from datetime import date
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.db.models import F
from core.decorators import retry_on_deadlock
from tenants.models import Tenant
from .models import Endpoint, UsageRecord, UsageSummary
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


class UsageService:
    @staticmethod
    def calculate_cost(
        *,
        endpoint: Endpoint,
        calls: int,
        data_bytes: int,
    ) -> Decimal:
        """
        Calculate the cost of a single usage event.
        """
        data_kb = Decimal(data_bytes) / Decimal(1024)

        return (
            endpoint.price_per_call * calls
            + endpoint.price_per_kb * data_kb
        )

    @staticmethod
    def get_current_period():
        """
        Returns the first day of the current month.
        Example:
            2026-07-09 -> 2026-07-01
        """
        today = date.today()
        return today.replace(day=1)

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
        Safely update the monthly usage summary.
        Thread-safe.
        """

        period = UsageService.get_current_period()

        try:
            summary = (
                UsageSummary.objects
                .select_for_update()
                .get(
                    tenant=tenant,
                    endpoint=endpoint,
                    period=period,
                )
            )

        except UsageSummary.DoesNotExist:
            try:
                summary = UsageSummary.objects.create(
                    tenant=tenant,
                    endpoint=endpoint,
                    period=period,
                )

            except IntegrityError:
                summary = (
                    UsageSummary.objects
                    .select_for_update()
                    .get(
                        tenant=tenant,
                        endpoint=endpoint,
                        period=period,
                    )
                )

        summary.total_calls = F("total_calls") + calls
        summary.total_bytes = F("total_bytes") + data_bytes
        summary.total_cost = F("total_cost") + cost

        summary.save(
            update_fields=[
                "total_calls",
                "total_bytes",
                "total_cost",
            ]
        )

        summary.refresh_from_db()

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
        """
        Store one immutable usage record.
        """

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

    from django.db.models import QuerySet
    @staticmethod
    def get_active_endpoint(*, tenant, endpoint_path: str) -> Endpoint:
        """
        Return an active endpoint for the given tenant.
        """
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
        Filtering, searching and pagination
        are handled by DRF backends.
        """

        return (
            UsageRecord.objects
            .filter(tenant=tenant)
            .select_related("user", "endpoint")
            .order_by("-timestamp")
        )




