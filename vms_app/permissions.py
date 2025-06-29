from rest_framework import permissions
from rest_framework.permissions import DjangoModelPermissions, BasePermission


class RedeemVoucherPermissions(permissions.BasePermission):
    """
    Custom permission that allows users to redeem vouchers (only for shop supervisors).
    """
    message = 'You are not allowed to redeem vouchers.'
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.has_perm('vms_app.redeem_voucher')
        )


class IsActiveUser(permissions.BasePermission):
    """
    Custom permission that allows access only to active users.
    """
    message = 'Your account is not active, you cannot access it.'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active


class CustomDjangoModelPermissions(permissions.BasePermission):
    """
        Allows access to users who have the permission 'view_<model_name>'
        for any model when making a GET request. For other methods, DjangoModelPermissions
        are applied.
    """

    def has_permission(self, request, view):
        # Check if the user is staff and the method is GET
        if request.user.is_staff and request.method == "GET":
            # Retrieve the model associated with the view
            model = view.queryset.model
            # Get the model's app label and model name (vms_app)
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            # Dynamically create the permission name in the format 'view_<model_name>'
            permission = f"{app_label}.view_{model_name}"
            # Check if the staff user has the permission to view this model
            if request.user.has_perm(permission):
                return True
            return False  # Return False if the staff user doesn't have the 'view_<model_name>' permission

        # For other methods (POST, PUT, DELETE), apply DjangoModelPermissions
        perms = DjangoModelPermissions()
        return perms.has_permission(request, view)


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

