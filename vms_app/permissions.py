from rest_framework.permissions import BasePermission

class IsSopSupervisor(BasePermission):
    """check if a user is a shop supervisor."""
    def has_permission(self, request, view):
        # the user must be a shop supervisor
        return request.user.groups.filter(name="shop_supervisor").exists()
