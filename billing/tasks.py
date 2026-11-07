import logging
from datetime import date
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import IntegrityError, OperationalError
from tenants.models import Tenant
from billing.services import BillingService
from billing.models import Invoice, SentNotification

logger = get_task_logger(__name__)




@shared_task(
    bind=True,
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=120,
    time_limit=180,
)
def generate_invoice_task(self, tenant_id: int, period_iso: str):
    logger.info(
        "start | tenant_id=%s period=%s retry=%s task_id=%s",
        tenant_id,
        period_iso,
        self.request.retries,
        self.request.id,
    )
    if self.request.retries < 2:
        logger.warning("💥 Fake Crash! Simulating a database deadlock...")
        raise OperationalError("Fake database deadlock for testing!")

    tenant = Tenant.objects.get(id=tenant_id)
    period = date.fromisoformat(period_iso)

    existing = Invoice.objects.filter(tenant=tenant, period=period).first()
    if existing:
        logger.info("skip | invoice_exists | tenant=%s invoice_id=%s", tenant.slug, existing.id)
        return existing.id

    try:
        invoice = BillingService.generate_invoice(tenant=tenant, period=period)
    except IntegrityError:
        invoice = Invoice.objects.get(tenant=tenant, period=period)
        logger.info("skip | integrity_error | tenant=%s invoice_id=%s", tenant.slug, invoice.id)
        return invoice.id

    BillingService.check_budget_alert(invoice=invoice)

    logger.info(
        "done | tenant=%s invoice_id=%s total=%s",
        tenant.slug,
        invoice.id,
        invoice.total,
    )
    return invoice.id







# ... (keep your existing imports and generate_invoice_task) ...

@shared_task
def generate_monthly_invoices():
    """
    Runs on the 1st of every month.
    Queues an invoice generation task for every active tenant.
    """
    # Get the 1st of the current month
    period = date.today().replace(day=1)
    tenants = Tenant.objects.filter(is_active=True)

    count = 0
    for tenant in tenants:
        # Queue the individual task we built in Phase 2
        generate_invoice_task.delay(tenant.id, period.isoformat())
        count += 1

    logger.info("Queued %s invoices for period %s", count, period)
    return f"Queued {count} invoices"


@shared_task
def send_invoice_email_task(invoice_id: int) -> dict:
    """
    Send the invoice email to the tenant.
    Idempotent — safe to run twice.
    """
    key = f"invoice_email:{invoice_id}"

    # 1. Check if already sent (Idempotency)
    if SentNotification.objects.filter(key=key).exists():
        logger.info("Email already sent for invoice_id=%s", invoice_id)
        return {"status": "already_sent"}

    # 2. Load invoice and send
    invoice = Invoice.objects.get(id=invoice_id)
    # (Placeholder for your actual email sending logic)
    print(f"📧 Sending email to {invoice.tenant.email} for invoice {invoice.id}")

    # 3. Record that we sent it
    try:
        SentNotification.objects.create(key=key)
    except IntegrityError:
        pass

    logger.info("Invoice email sent for invoice_id=%s", invoice_id)
    return {"status": "sent"}
