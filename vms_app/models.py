from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import MaxValueValidator
from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class Company(models.Model):
    company_name = models.CharField(max_length=70)
    prefix = models.CharField(max_length=3, blank=True, null=True )
    company_logo = models.BinaryField(blank=True, null=True)
    vat = models.CharField(max_length=8, blank=True, null=True)
    brn = models.CharField(max_length=9, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    tel = models.CharField(max_length=8, blank=True, null=True)


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

    signature = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return self.username


class Client(models.Model):
    iscompany = models.BooleanField(default=True)
    clientname = models.CharField(max_length=70)
    vat = models.CharField(max_length=8)
    brn = models.CharField(max_length=9)
    nic = models.CharField(max_length=14, blank=True, null=True)
    email = models.EmailField(max_length=50)
    contact = models.CharField(max_length=70)
    logo = models.BinaryField(blank=True, null=True)

    class Meta:
        ordering = ['clientname']

    def __str__(self):
        return f"{self.clientname}"


class VoucherRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class Meta:
        ordering = ['request_ref']
        permissions = [
            ("reject_request", "Can reject a voucher request"),
            ("approve_request", "Can approve a voucher request"),
            ("change_to_paid", "Can change the request_status from pending to paid"),
        ]

    request_ref = models.TextField(unique=True, blank=True, null=True)
    date_time_recorded = models.DateTimeField(default=timezone.now, blank=True)
    quantity_of_vouchers = models.IntegerField(blank=False, null=False, default=1)
    amount = models.IntegerField(null=True, blank=True)
    request_status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    date_time_approved = models.DateTimeField(null=True, blank=True)
    request_doc_pdf = models.FileField(
        upload_to='voucher_requests/doc/',
        null=True,
        blank=True,
        help_text='PDF of email received from the initiating client'
    )
    pop_doc_pdf = models.FileField(upload_to='voucher_requests/pop/', null=True, blank=True,
                                   help_text='PDF of PoP received from the client')
    payment_remarks = models.TextField(null=True, blank=True)
    date_time_paid = models.DateTimeField(null=True, blank=True)

    recorded_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_voucher_requests', null=True, blank=True
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='approved_requests', null=True, blank=True
    )

    client = models.ForeignKey(
        'Client', on_delete=models.CASCADE, null=True, blank=True,
        related_name='client_voucher_requests'
    )

    company = models.ForeignKey(
        'Company', on_delete=models.CASCADE, null=True, blank=True,
        related_name='voucher_requests'
    )

    validity_periode = models.IntegerField(
        validators=[MaxValueValidator(12)],
        null=True, blank=True, default=1,
        help_text="Validity period in months from the date of approval (1 to 12 months)"
    )


    def save(self, *args, **kwargs):
        if not self.request_ref and self.company:
            for _ in range(5):  # Retry 5 times if a duplicate error occurs
                self.request_ref = self.generate_request_ref()
                try:
                    super().save(*args, **kwargs)
                    return
                except IntegrityError as e:
                    if 'duplicate key value violates unique constraint' in str(e):
                        continue  # Try again with a new sequence
                    else:
                        raise
            raise IntegrityError("Failed to generate a unique request_ref after multiple attempts.")
        else:
            super().save(*args, **kwargs)

    def generate_request_ref(self):
        year_suffix = timezone.now().strftime('%y')
        company_prefix = self.company.prefix.upper()

        # Get all refs from the current year (regardless of company)
        year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        all_refs = VoucherRequest.objects.filter(
            date_time_recorded__gte=year_start
        ).values_list('request_ref', flat=True)

        sequence = 1
        for ref in sorted(all_refs, reverse=True):
            try:
                parts = ref.split('-')
                if len(parts) == 4 and parts[2] == year_suffix:
                    sequence = int(parts[3].replace('#', '')) + 1
                    break
            except Exception:
                continue

        return f"VRQ-{company_prefix}-{year_suffix}-#{sequence}"

    def clean(self):
        if self.pk:
            old_status = VoucherRequest.objects.get(pk=self.pk).request_status

            if old_status in ('approved', 'rejected') and self.request_status != old_status:
                raise ValidationError(f"Invalid status: {old_status} requests cannot modified")

            if old_status == 'pending' and self.request_status not in ('paid', 'rejected', 'pending'):
                raise ValidationError("Invalid status: pending requests can only be paid or rejected")

            if old_status == 'paid' and self.request_status not in ('paid', 'rejected', 'approved'):
                raise ValidationError("Invalid status: pending requests can only be approved or rejected")

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
        permissions = [("redeem_voucher", "Can redeem voucher")]

    voucher_request = models.ForeignKey(VoucherRequest, on_delete=models.CASCADE, related_name='vouchers')
    voucher_ref = models.TextField(unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_time_created = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateField(blank=True, null=True)
    extention_date = models.DateField(null=True, blank=True)
    voucher_status = models.CharField(max_length=20, choices=VoucherStatus.choices, default=VoucherStatus.PROVISIONAL)

    def redeem(self, user, shop, till_no):
        """Redeem the voucher by creating a Redemption and updating status."""
        if not user.has_perm('vms_app.redeem_voucher'):
            raise PermissionDenied("You do not have permission to redeem vouchers.")

        if self.voucher_status != Voucher.VoucherStatus.ISSUED:
            raise ValueError("Voucher must be issued to be redeemed.")
        # Create the Redemption
        Redemption.objects.create(voucher=self, user=user, shop=shop, till_no=till_no)
        # Update voucher status to redeemed
        self.voucher_status = Voucher.VoucherStatus.REDEEMED
        self.save()

    @extend_schema_field(serializers.CharField)
    def get_redemption_info(self):
        redemption = self.redemption  # Accéder à la relation Redemption
        if redemption:
            # Formater la date pour qu'elle soit plus conviviale
            redemption_date = localtime(redemption.redemption_date)
            formatted_date = redemption_date.strftime('%d %b %Y, %H:%M')  # Format: 02 Feb 2025, 14:39
            return f"Redeemed on {formatted_date}; at {redemption.shop.company.company_name} {redemption.shop.location}"
        return "No redemption"
    get_redemption_info.short_description = 'Redemption'

    def __str__(self):
        return f"Ref: {self.voucher_ref};\n Amount: {self.amount} MUR"

    def save(self, *args, **kwargs):
        if not self.voucher_ref:
            self.voucher_ref = self.generate_voucher_ref()
        super().save(*args, **kwargs)

    def generate_voucher_ref(self):
        from django.utils.timezone import now
        year_suffix = now().strftime('%y')
        prefix = self.voucher_request.company.prefix.upper()

        base_code = f"{prefix}-{year_suffix}"
        similar_refs = Voucher.objects.filter(
            voucher_ref__startswith=base_code
        ).values_list('voucher_ref', flat=True)

        max_seq = 0
        for ref in similar_refs:
            try:
                parts = ref.split('-')
                if len(parts) == 3 and parts[0] == prefix and parts[1] == year_suffix:
                    seq = int(parts[2])
                    if seq > max_seq:
                        max_seq = seq
            except:
                continue

        new_seq = str(max_seq + 1).zfill(4)
        return f"{prefix}-{year_suffix}-{new_seq}"


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
        return (f"Ref: {self.voucher.voucher_ref}, "
            f"redeemed_on: {self.redemption_date}, "
            f"redeemed at: {self.shop.company.company_name} {self.shop.location}")


class AuditTrail(models.Model):
    class AuditTrailsAction(models.TextChoices):
        ADD = 'add', 'Add'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'

    class Meta:
        ordering = ['datetime']

    datetime = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_trails')
    table_name = models.CharField(max_length=20, null=True, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    action = models.CharField(
        max_length=10,
        choices=AuditTrailsAction.choices,
        null=True, blank=True
    )

    def __str__(self):
        return f"user: {self.user.username}, table_name: {self.table_name}, action: {self.action}"
