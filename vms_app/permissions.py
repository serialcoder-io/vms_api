from rest_framework import permissions

class RedeemVoucherPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not request.user.has_perm('vms_app.redeem_voucher'):
            return False
        return True