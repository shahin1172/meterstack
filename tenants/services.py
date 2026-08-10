from django.utils.text import slugify
from tenants.models import Tenant
from users.models import User


def create_tenant_with_admin(
    *,
    tenant_name: str,
    tenant_slug: str | None = None,
    admin_username: str,
    admin_email: str,
    admin_password: str,
) -> tuple[Tenant, User]:
    """Create a new Tenant and its admin User in one atomic operation."""
    if not tenant_slug:
        tenant_slug = slugify(tenant_name)

    tenant = Tenant.objects.create(name=tenant_name, slug=tenant_slug)
    admin = User.objects.create_user(
        username=admin_username,
        email=admin_email,
        password=admin_password,
        tenant=tenant,
        role=User.Role.ADMIN,
    )
    return tenant, admin