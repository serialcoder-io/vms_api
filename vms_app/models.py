from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    company_name = models.CharField(max_length=70)

    def __str__(self):
        return self.company_name


class Shop(models.Model):
    location = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='shops')


class User(AbstractUser):
    REQUIRED_FIELDS = ['email']
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return self.username


class Client(models.Model):
    firstname = models.CharField(max_length=70)
    lastname = models.CharField(max_length=70)
    email = models.EmailField(max_length=50)
    contact = models.CharField(max_length=13)
    logo = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class VoucherRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_voucher_requests',
        null=False, blank=False
    )
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_requests', null=True)
    request_ref = models.TextField(unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_voucher_requests')
    date_time_captured = models.DateTimeField(auto_now_add=True)
    date_time_approved = models.DateTimeField(null=True)
    request_status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )


class PendingVoucher(models.Model):
    voucher_request = models.ForeignKey(VoucherRequest, on_delete=models.CASCADE, related_name='pending_vouchers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    expiration_date = models.DateField()


class Voucher(models.Model):
    class VoucherStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED= 'expired', 'Expired'
        REDEEMDED = 'redeemed', 'Redeemed'

    voucher_request = models.ForeignKey(VoucherRequest, on_delete=models.CASCADE, related_name='vouchers')
    voucher_ref = models.TextField(unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(blank=False, null=False)
    extention_date = models.DateField(null=True)
    voucher_status = models.CharField(
        max_length=20,
        choices=VoucherStatus.choices,
        default=VoucherStatus.ACTIVE
    )
    redeem_on = models.DateTimeField(null=True)


class Redemption(models.Model):
    voucher = models.ForeignKey(
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
    redemption_date = models.DateTimeField(auto_now_add=True)
    till_no = models.IntegerField(blank=False, null=True)


class AuditTrails(models.Model):
    class AuditTrailsAction(models.TextChoices):
        ADD = 'add', 'Add'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'

    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_trails')
    action = models.CharField(
        max_length=10,
        choices=AuditTrailsAction.choices,
        null=True, blank=False
    )
    table_name = models.CharField(max_length=20)
    object_id = models.IntegerField()
    description = models.TextField()
