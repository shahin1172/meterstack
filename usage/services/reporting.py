from __future__ import annotations
import logging
import time
from datetime import date
from typing import Any, Callable
from django.core.cache import cache
from tenants.models import Tenant
from usage.models import UsageRecord, UsageSummary
from datetime import date
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class ReportingService:
    """
    Provides reporting queries used by dashboard APIs.
    """

    SLOW_QUERY_THRESHOLD = 0.5

    CACHE_TIMEOUT = 300
    CACHE_PREFIX = "dashboard"

    @classmethod
    def _log_query_time(
        cls,
        query_name: str,
        started_at: float,
    ) -> None:
        """
        Log slow queries.
        """

        elapsed = time.perf_counter() - started_at

        if elapsed >= cls.SLOW_QUERY_THRESHOLD:
            logger.warning(
                "%s took %.3f seconds",
                query_name,
                elapsed,
            )

    @classmethod
    def _get_or_set_cache(
        cls,
        *,
        key: str,
        callback: Callable[[], Any],
    ) -> Any:
        """
        Cache-Aside helper.
        """

        cached_data = cache.get(key)

        if cached_data is not None:
            logger.info(
                "Cache HIT | %s",
                key,
            )
            return cached_data

        logger.info(
            "Cache MISS | %s",
            key,
        )

        result = callback()

        cache.set(
            key,
            result,
            timeout=cls.CACHE_TIMEOUT,
        )

        return result

    @classmethod
    def invalidate_dashboard_cache(
        cls,
        tenant: Tenant,
    ) -> None:
        """
        Remove all cached dashboard data for a tenant.

        Called whenever usage data changes so the next dashboard
        request is rebuilt from the database.
        """

        current_period = date.today().replace(day=1)
        previous_period = current_period - relativedelta(months=1)

        keys = [
            (
                f"{cls.CACHE_PREFIX}:"
                f"top_endpoints:"
                f"{tenant.slug}:5"
            ),
            (
                f"{cls.CACHE_PREFIX}:"
                f"daily_trends:"
                f"{tenant.slug}:30"
            ),
            (
                f"{cls.CACHE_PREFIX}:"
                f"compare_periods:"
                f"{tenant.slug}:"
                f"{current_period}:"
                f"{previous_period}"
            ),
        ]

        cache.delete_many(keys)

        logger.info(
            "Dashboard cache invalidated | tenant=%s",
            tenant.slug,
        )

    @classmethod
    def get_top_endpoints(
        cls,
        tenant: Tenant,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the most used endpoints.
        """

        started = time.perf_counter()

        cache_key = (
            f"{cls.CACHE_PREFIX}:"
            f"top_endpoints:"
            f"{tenant.slug}:"
            f"{limit}"
        )

        def query():
            return UsageSummary.objects.top_endpoints(
                tenant=tenant,
                limit=limit,
            )

        result = cls._get_or_set_cache(
            key=cache_key,
            callback=query,
        )

        cls._log_query_time(
            "get_top_endpoints",
            started,
        )

        return result

    @classmethod
    def get_daily_usage_trends(
        cls,
        tenant: Tenant,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Return daily usage trends.
        """

        started = time.perf_counter()

        cache_key = (
            f"{cls.CACHE_PREFIX}:"
            f"daily_trends:"
            f"{tenant.slug}:"
            f"{days}"
        )

        def query():
            return UsageRecord.objects.daily_trends(
                tenant=tenant,
                days=days,
            )

        result = cls._get_or_set_cache(
            key=cache_key,
            callback=query,
        )

        cls._log_query_time(
            "get_daily_usage_trends",
            started,
        )

        return result

    @classmethod
    def compare_periods(
        cls,
        tenant: Tenant,
        current_period: date,
        previous_period: date,
    ) -> dict[str, Any]:
        """
        Compare two reporting periods.
        """

        started = time.perf_counter()

        cache_key = (
            f"{cls.CACHE_PREFIX}:"
            f"compare_periods:"
            f"{tenant.slug}:"
            f"{current_period}:"
            f"{previous_period}"
        )

        def query():
            return UsageSummary.objects.compare_periods(
                tenant=tenant,
                current_period=current_period,
                previous_period=previous_period,
            )

        result = cls._get_or_set_cache(
            key=cache_key,
            callback=query,
        )

        cls._log_query_time(
            "compare_periods",
            started,
        )

        return result