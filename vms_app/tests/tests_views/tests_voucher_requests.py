from typing import assert_never

from django.contrib.auth.models import Permission, Group
# from django.db.models import Max
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from vms_app.models import User, VoucherRequest, Voucher, Client


class ClientViewsTestCase(TestCase):
    def setUp(self):
        self.voucher_request_list_url = "/vms/api/voucher_requests"
        self.voucher_request_post_url = "/vms/api/voucher_requests/add/"
        # Create a test user
        user1 = User.objects.create_user(username='user_with_perms', password='password')
        # create user with no permission
        user_without_perms = User.objects.create_user(
            username='user_without_perms',
            password='password'
        )

        # Add Django ModelPermissions for this user
        permissions = Permission.objects.filter(codename__in=[
            'view_voucherrequest',
            'add_voucherrequest',
            'change_voucherrequest',
            'delete_voucherrequest',
        ])
        user1.user_permissions.add(*permissions)

        # Create a client for testing
        client1 = Client.objects.create(
            firstname="client1_firstname",
            lastname="client1_lastname",
            email="client1-emails@gmail.com",
            contact="+230 5429 7857",
        )

        VoucherRequest.objects.create(
            quantity_of_vouchers= 2,
            amount= 1000,
            recorded_by=user1,
            client=client1,
        )
        # Initialize API client for testing
        self.client = APIClient()

    def test_voucher_request_list_authenticated_user_with_permissions(self):
        # Log in with the test user
        self.client.login(username='user_with_perms', password='password')
        # Make a GET request to the voucher requests list endpoint
        response = self.client.get(f"{self.voucher_request_list_url}/")
        # Check that the response status code is 200 (OK)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            "Expected status code 200, but got {0}".format(response.status_code)
        )
        self.client.logout()

    def test_voucher_request_list_user_not_authenticated(self):
        # Log in with the test user without permissions

        # Make a GET request to the voucher requests list endpoint
        response = self.client.get(f"{self.voucher_request_list_url}/")
        # Check that the response status code is 401 (UNAUTHORIZED)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            "Expected status code 401, but got {0}".format(response.status_code)
        )

    def test_generate_vouchers_after_created_voucher_request(self):
        self.client.login(username='user_with_perms', password='password')
        user = User.objects.get(username='user_with_perms')
        client = Client.objects.create(
            firstname="client_firstname",
            lastname="client_lastname",
            email="client-emails@gmail.com",
            contact="+230 5429 7857",
        )
        response = self.client.post(self.voucher_request_post_url, {
            "quantity_of_vouchers":  2,
            "amount": 1000,
            "recorded_by": user.id,
            "client": client.id,
        }, format='json')
        data = response.json()
        voucher_request = VoucherRequest.objects.get(pk=data['id'])
        related_vouchers = voucher_request.vouchers.count()
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            "Expected status code 201, but got {0}".format(response.status_code)
        )
        self.assertEqual(
            data['request_status'], 'pending',
            "the default status of voucher_request must be pending"
        )
        self.assertEqual(
            related_vouchers, 2,
            "The number of related vouchers must be equal to quantity_of_vouchers (2)"
        )


    def test_change_voucher_request_status_to_paid(self):
        self.client.login(username='user_with_perms', password='password')
        user = User.objects.get(username='user_with_perms')
        client = Client.objects.create(
            firstname="client_firstname",
            lastname="client_lastname",
            email="client-emails@gmail.com",
            contact="+230 5429 7857",
        )
        # approver group(after the request status change from pending to pending,
        request_approver_group, created = Group.objects.get_or_create(name='request_approver')
        user.groups.add(request_approver_group)
        response = self.client.post(self.voucher_request_post_url, {
            "quantity_of_vouchers": 2,
            "amount": 1000,
            "recorded_by": user.id,
            "client": client.id,
        }, format='json')
        data = response.json()
        request_id = data["id"]
        new_response = self.client.put(f"{self.voucher_request_list_url}/{request_id}/", {
            "request_status": 'paid',
        })
        voucher_request_after_update = self.client.get(f"{self.voucher_request_list_url}/{request_id}/")
        new_data = voucher_request_after_update.json()

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            "Expected status code 200, but got {0}".format(response.status_code)
        )
        self.assertEqual(
            new_data["request_status"], 'paid',
            "expected request_status = 'paid'"
        )
