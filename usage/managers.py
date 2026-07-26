from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from django.db import models
from django.db.models import Sum
from django.db.models.functions import TruncDate
from tenants.models import Tenant


class UsageRecordManager(models.Manager):
    """
    Query helpers for raw UsageRecord data.
    """

    def daily_trends(
        self,
        *,
        tenant: Tenant,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Return daily usage statistics for the last N days.
        """

        start_date = date.today() - timedelta(days=days)

        return list(
            self.filter(
                tenant=tenant,
                timestamp__date__gte=start_date,
            )
            .annotate(
                day=TruncDate("timestamp"),
            )
            .values(
                "day",
            )
            .annotate(
                total_calls=Sum("calls"),
                total_cost=Sum("cost"),
            )
            .order_by("day")
        )

    def current_month_usage(
        self,
        *,
        tenant: Tenant,
    ) -> dict[str, Any]:
        """
        Return current month's total usage directly
        from UsageRecord.
        """

        current_period = date.today().replace(day=1)

        result = self.filter(
            tenant=tenant,
            timestamp__date__gte=current_period,
        ).aggregate(
            total_calls=Sum("calls"),
            total_cost=Sum("cost"),
            total_bytes=Sum("data_bytes"),
        )

        return {
            "total_calls": result["total_calls"] or 0,
            "total_cost": result["total_cost"] or Decimal("0"),
            "total_bytes": result["total_bytes"] or 0,
        }


class UsageSummaryManager(models.Manager):
    """
    Query helpers for aggregated monthly usage.
    """

    def top_endpoints(
        self,
        *,
        tenant: Tenant,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the most used endpoints.
        """

        return list(
            self.filter(
                tenant=tenant,
            )
            .values(
                "endpoint__name",
            )
            .annotate(
                total_calls=Sum("total_calls"),
                total_cost=Sum("total_cost"),
            )
            .order_by("-total_calls")[:limit]
        )

    def compare_periods(
        self,
        *,
        tenant: Tenant,
        current_period: date,
        previous_period: date,
    ) -> dict[str, Any]:
        """
        Compare two billing periods.
        """

        current = (
            self.filter(
                tenant=tenant,
                period=current_period,
            )
            .aggregate(
                total_calls=Sum("total_calls"),
                total_cost=Sum("total_cost"),
                total_bytes=Sum("total_bytes"),
            )
        )

        previous = (
            self.filter(
                tenant=tenant,
                period=previous_period,
            )
            .aggregate(
                total_calls=Sum("total_calls"),
                total_cost=Sum("total_cost"),
                total_bytes=Sum("total_bytes"),
            )
        )

        return {
            "current": {
                "total_calls": current["total_calls"] or 0,
                "total_cost": current["total_cost"] or Decimal("0"),
                "total_bytes": current["total_bytes"] or 0,
            },
            "previous": {
                "total_calls": previous["total_calls"] or 0,
                "total_cost": previous["total_cost"] or Decimal("0"),
                "total_bytes": previous["total_bytes"] or 0,
            },
        }