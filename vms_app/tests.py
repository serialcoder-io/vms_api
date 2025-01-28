from django.db.models import Max
from django.test import Client, TestCase

from .models import (
    User,
    Client,
    VoucherRequest,
    Voucher,
    #Redemption,
    Company,
    #Shop
)

# models
class VoucherRequestTestCase(TestCase):
    def setUp(self):
        client_1 = Client.objects.create(
            firstname="client1_firstname",
            lastname="client1_lastname",
            email="client1-email@gmail.com",
            contact="+230 5429 7857",
        )
        conpany_1 = Company.objects.create(company_name="company-1")
        user = User.objects.create_user(
            username="user-1",
            first_name="user1_firstname",
            last_name="user1_lastname",
            email="user1@gmail.com",
            password="Strong-P4$5word",
            company=conpany_1,
        )
        voucher_request = VoucherRequest.objects.create(
            recorded_by=user,
            request_ref="VRQ-00001-1/3",
            client=client_1,
            quantity_of_vouchers=3,
        )
        voucher1 = Voucher.objects.create(
            voucher_request=voucher_request,
            voucher_ref="VR-00001-1000",
            amount=1000,
            expiry_date="2025-09-20",
        )

    def test_voucher_request_count(self):
        success_message = "The number of `VoucherRequest` should be 1."
        self.assertEqual(VoucherRequest.objects.count(), 1, success_message)

        fail_message = "The number of `VoucherRequest` should not be 0."
        self.assertNotEqual(VoucherRequest.objects.count(), 0, fail_message)

    def test_voucher_request_default_status(self):
        voucher_request = VoucherRequest.objects.get(request_ref="VRQ-00001-1/3")
        message = "The default status of a `VoucherRequest` should be 'pending'."
        self.assertEqual(voucher_request.request_status, "pending", message)

    def test_voucher_default_status(self):
        voucher = Voucher.objects.get(voucher_ref="VR-00001-1000")
        self.assertEqual(
            voucher.voucher_status,
            "provisional",
            "default status should be provisional."
        )
