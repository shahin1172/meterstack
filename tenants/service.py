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
    """
    Create a new Tenant and its admin User in one atomic operation.

    If tenant_slug is not provided, it is generated automatically from
    the tenant_name using Django's slugify().
    The admin user's password is securely hashed by create_user().
    """
    # Generate slug if missing or empty
    if not tenant_slug:
        tenant_slug = slugify(tenant_name)

    # 1. Create the tenant
    tenant = Tenant.objects.create(
        name=tenant_name,
        slug=tenant_slug,
    )

    # 2. Create the admin user
    admin = User.objects.create_user(
        username=admin_username,
        email=admin_email,
        password=admin_password,        # hashed automatically
        tenant=tenant,
        role=User.Role.ADMIN,           # or 'admin' (string) depending on your model
    )

    return tenant, admin