from django.test import Client, TestCase

from vms_app.models import (
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
        new_client = Client.objects.create(
            clientname="new_client",
            vat="vat#1",
            brn="brn_cl",
            nic="nic_cli",
            email="new_client-emails@gmail.com",
            contact="+230 5429 7857",
        )
        new_conpany = Company.objects.create(company_name="new_company", prefix="NCP")
        user = User.objects.create_user(
            username="new_user",
            first_name="user_firstname",
            last_name="user_lastname",
            email="new_user@gmail.com",
            password="Strong-P4$5word",
            company=new_conpany,
        )
        voucher_request = VoucherRequest.objects.create(
            recorded_by=user,
            request_ref="VRQ-00001-1/1",
            client=new_client,
            quantity_of_vouchers=3,
        )
        Voucher.objects.create(
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
        voucher_request = VoucherRequest.objects.get(request_ref="VRQ-00001-1/1")
        message = "The default status of a `VoucherRequest` should be 'pending'."
        self.assertEqual(voucher_request.request_status, "pending", message)

    def test_voucher_default_status(self):
        voucher = Voucher.objects.get(voucher_ref="VR-00001-1000")
        self.assertEqual(
            voucher.voucher_status,
            "provisional",
            "default status should be provisional."
        )

"""class RedemptionTestCase(TestCase):
    def setUp(self):
        pass"""