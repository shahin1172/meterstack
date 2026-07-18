from rest_framework import permissions
from .models import User
from rest_framework.permissions import BasePermission


#permission that ensures users can only access objects belonging to their own tenant.
class IsInSameTenant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # must be authenticated and obj must have tenant
        return (
            request.user.is_authenticated
            and hasattr(obj, 'tenant')
            and request.user.tenant == obj.tenant
        )


#a permission to restrict member signup to tenant admins
class Adminrestriction(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request . user . role == User . Role . ADMIN

class IsTenantAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'admin'   # or User.Role.ADMIN
        )





class IsTenantAdmin(BasePermission):
    """
    Allows access only to tenant administrators.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )