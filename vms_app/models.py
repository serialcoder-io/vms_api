from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.utils import timezone


class Company(models.Model):
    company_name = models.CharField(max_length=70)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class Shop(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shops')
    location = models.CharField(max_length=100)
    address = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.company.company_name} {self.location}"


class User(AbstractUser):
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['username', 'email']

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        null=True
    )

    def __str__(self):
        return self.username


class Client(models.Model):
    firstname = models.CharField(max_length=70)
    lastname = models.CharField(max_length=70)
    email = models.EmailField(max_length=50)
    contact = models.CharField(max_length=20)
    logo = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['lastname', 'firstname']

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class VoucherRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class Meta:
        ordering = ['request_ref']

    recorded_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_voucher_requests', null=True, blank=True
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='approved_requests', null=True, blank=True
    )
    request_ref = models.TextField(unique=True, blank=True, null=True)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, blank=True,
        related_name='client_voucher_requests'
    )
    request_status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    date_time_recorded = models.DateTimeField(default=timezone.now, blank=True)
    quantity_of_vouchers = models.IntegerField(blank=False, null=False, default=1)
    description = models.TextField(blank=True, null=True)
    date_time_approved = models.DateTimeField(null=True, blank=True)

    def set_date_time_approved(self):
        """Set the approval timestamp when the request is approved."""
        self.date_time_approved = timezone.now()
        self.save()

    def update_related_vouchers_status(self, new_request_status):
        """
        Updates the status of vouchers linked to the voucher request within a transaction.

        This method checks for vouchers with a 'PROVISIONAL' status and updates them based on the
        new status of the voucher request (approved or rejected).
        """
        try:
            with transaction.atomic():
                # Filter provisional vouchers linked to this request
                provisional_related_vouchers = self.vouchers.filter(
                    voucher_status=Voucher.VoucherStatus.PROVISIONAL
                )

                if provisional_related_vouchers.exists():
                    # Only proceed with updating if the request status is 'pending'
                    if self.request_status == "pending":
                        updated_count = 0

                        # Update voucher status based on the new request status
                        if new_request_status == "approved":
                            updated_count = provisional_related_vouchers.update(
                                voucher_status=Voucher.VoucherStatus.ISSUED
                            )
                        elif new_request_status == "rejected":
                            updated_count = provisional_related_vouchers.update(
                                voucher_status=Voucher.VoucherStatus.CANCELLED
                            )

                        # Raise an exception if no vouchers were updated
                        if updated_count == 0:
                            raise ValueError("No provisional vouchers were updated.")
                else:
                    # No provisional vouchers found, simply leave their status unchanged
                    for voucher in provisional_related_vouchers:
                        voucher.voucher_status = voucher.voucher_status

        except Exception as e:
            # Log or raise a more specific error to help with debugging
            raise Exception(f"Error while updating voucher status: {e}")

    def __str__(self):
        return f"Voucher Request ref: {self.request_ref}"


class Voucher(models.Model):
    class VoucherStatus(models.TextChoices):
        PROVISIONAL = 'provisional', 'Provisional'
        ISSUED = 'issued', 'Issued'
        EXPIRED = 'expired', 'Expired'
        REDEEMED = 'redeemed', 'Redeemed'
        CANCELLED = 'cancelled', 'Cancelled'

    class Meta:
        ordering = ['voucher_ref']

    voucher_request = models.ForeignKey(VoucherRequest, on_delete=models.CASCADE, related_name='vouchers')
    voucher_ref = models.TextField(unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time_created = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField(blank=False, null=False)
    extention_date = models.DateField(null=True, blank=True)
    voucher_status = models.CharField(
        max_length=20,
        choices=VoucherStatus.choices,
        default=VoucherStatus.PROVISIONAL
    )

    def redeem(self, user, shop, till_no):
        """Redeem the voucher by creating a Redemption and updating status."""
        if self.voucher_status != Voucher.VoucherStatus.ISSUED:
            raise ValueError("Voucher must be issued to be redeemed.")
        # Create the Redemption
        Redemption.objects.create(voucher=self, user=user, shop=shop, till_no=till_no)
        # Update voucher status to redeemed
        self.voucher_status = Voucher.VoucherStatus.REDEEMED
        self.save()

    def __str__(self):
        return f"Ref: {self.voucher_ref}; Amount: {self.amount} MUR"


class Redemption(models.Model):
    voucher = models.OneToOneField(
        Voucher, on_delete=models.CASCADE,
        related_name='redemption',
        null=True, blank=False
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_redemptions',
        null=False, blank=False
    )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shop_redemptions')
    redemption_date = models.DateTimeField(default=timezone.now)
    till_no = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return (f"voucher_ref: {self.voucher.voucher_ref}, "
            f"redeemed_on: {self.redemption_date}, "
            f"shop: {self.shop.company.company_name} {self.shop.location}")


class AuditTrails(models.Model):
    class AuditTrailsAction(models.TextChoices):
        ADD = 'add', 'Add'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'

    class Meta:
        ordering = ['datetime']

    datetime = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_trails')
    table_name = models.CharField(max_length=20)
    object_id = models.IntegerField()
    description = models.TextField()
    action = models.CharField(
        max_length=10,
        choices=AuditTrailsAction.choices,
        null=True, blank=False
    )

    def __str__(self):
        return f"user: {self.user.username}, table_name: {self.table_name}, action: {self.action}"
