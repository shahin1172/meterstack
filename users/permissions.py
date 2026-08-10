from rest_framework.permissions import BasePermission


class IsInSameTenant(BasePermission):
    """
    Object‑level permission – ensure the requesting user and the object
    belong to the same tenant.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and hasattr(obj, 'tenant')
            and request.user.tenant == obj.tenant
        )


class IsTenantAdmin(BasePermission):
    """
    Allows access only to tenant administrators (role == 'admin').
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )