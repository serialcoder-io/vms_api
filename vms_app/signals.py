from django.db.models.signals import post_save
from django.dispatch import receiver

from vms_app.models import VoucherRequest, Voucher

@receiver(post_save, sender=VoucherRequest)
def create_vouchers(sender, instance, created, **kwargs):
    """Create vouchers after a VoucherRequest is saved."""
    if created:  # Ensure that the VoucherRequest has just been created
        for _ in range(instance.quantity_of_vouchers):  # Loop through the requested quantity of vouchers
            # Create a voucher with the same amount and expiry date as the VoucherRequest
            Voucher.objects.create(
                voucher_request=instance,
                amount=instance.amount,
                expiry_date=instance.vouchers_expiry_date
            )
