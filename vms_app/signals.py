from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from vms_app.models import VoucherRequest, Voucher
from datetime import date, timedelta

from vms_app.utils import notify_requests_approvers


@receiver(post_save, sender=VoucherRequest)
def create_vouchers(instance, created, **kwargs):
    if created:
        # Automatically generate vouchers after a voucher request has been registered.
        amount = instance.amount
        for _ in range(instance.quantity_of_vouchers):
            Voucher.objects.create(
                voucher_request=instance,
                amount=amount,
                voucher_status='provisional',
            )


@receiver(pre_save, sender=VoucherRequest)
def update_voucher_expiry_and_status_after_request_approval(instance, **kwargs):
    if instance.pk:
        # Retrieve the old instance before it is updated.
        old_instance = VoucherRequest.objects.get(pk=instance.pk)
        old_status = old_instance.request_status
        new_status = instance.request_status
        validity_type = instance.validity_type
        validity_periode = int(instance.validity_periode)

        if validity_type == "week":
            vouchers_expiry_date = date.today() + timedelta(days=validity_periode * 7)
        else:
            vouchers_expiry_date = date.today() + timedelta(days=validity_periode * 30)

        # Si le statut passe de 'paid' à 'approved', on met à jour les vouchers
        if old_status == 'paid' and new_status == 'approved':
            queryset = Voucher.objects.filter(voucher_request=instance)
            queryset.update(expiry_date=vouchers_expiry_date, voucher_status="issued")
            instance.date_time_approved = timezone.now()
        if old_status != 'rejected' and new_status == 'rejected':
            queryset = Voucher.objects.filter(voucher_request=instance)
            queryset.update(voucher_status="cancelled")

        if old_status == 'pending' and new_status == 'paid':
            """ 
                Notify all users with approval rights when a voucher request status changes from 'pending' to 'paid'
            """
            notify_requests_approvers(instance.request_ref)