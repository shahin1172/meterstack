import logging
from celery import shared_task
from tenants.models import Tenant
from usage.services.reporting import ReportingService

logger = logging.getLogger(__name__)

@shared_task
def invalidate_dashboard_cache_task(tenant_id: int) -> None:
    """
    Invalidate the cached dashboard data for a tenant.
    Called after a usage record is committed.
    """
    tenant = Tenant.objects.get(id=tenant_id)
    ReportingService.invalidate_dashboard_cache(tenant)
    logger.info("Dashboard cache invalidated for tenant=%s", tenant.slug)


@shared_task
def warm_all_dashboards():
    """
    Runs every night at 2:30 AM.
    Pre-calculates dashboard data for all active tenants.
    """
    tenants = Tenant.objects.filter(is_active=True)
    for tenant in tenants:
        # This forces the service to calculate and save to cache
        ReportingService.get_top_endpoints(tenant=tenant)
        ReportingService.get_daily_usage_trends(tenant=tenant)

    logger.info("Warmed dashboard caches for %s tenants", tenants.count())