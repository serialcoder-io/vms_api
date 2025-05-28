from django.contrib.auth.models import Permission
# from django.db.models import Max
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from vms_app.models import User, Client

class ClientViewsTestCase(TestCase):
    def setUp(self):
        self.client_list_url = "/vms/api/clients/"
        # Create a test user
        user1 = User.objects.create_user(username='testuser', password='testpassword')
        # create a user with no permission
        User.objects.create_user(username='testuser2', password='testpassword')

        # Add Django ModelPermissions for this user
        permissions = Permission.objects.filter(codename__in=[
            'view_client',
            'add_client',
            'change_client',
            'delete_client',
        ])
        user1.user_permissions.add(*permissions)

        # Create a client for testing
        Client.objects.create(
            clientname="new_client1",
            vat="vat12",
            brn="brn_cli1",
            nic="nic_cli1",
            email="new_client1-emails@gmail.com",
            contact="+230 5429 7857",
        )
        # Initialize API client for testing
        self.client = APIClient()


    def test_client_list_authenticated_user_with_permissions(self):
        # Log in with the test user
        self.client.login(username='testuser', password='testpassword')
        # Make a GET request to the client list endpoint
        response = self.client.get(self.client_list_url)
        # Check that the response status code is 200 (OK)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            "Expected status code 200, but got {0}".format(response.status_code)
        )


    def test_client_list_unauthenticated_user(self):
        # Make a GET request to the client list endpoint without authentication
        response = self.client.get(self.client_list_url)

        # Check that the response status code is 401 (Unauthorized)
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED,
            "Expected status code 401, but got {0}".format(response.status_code)
        )


    def test_add_client_authenticated_user_with_permission(self):
        # Login with the test user
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(f"{self.client_list_url}add/", {
            "clientname": "new_client",
            "vat": "vat34",
            "brn": "brn_cli",
            "nic": "nic_cli",
            "email": "new_client-emails@gmail.com",
            "contact": "+230 5429 7857",
        }, format='json')

        data = response.json()

        # Assert that the response code is 201 after created new user
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            f"Expected status code 201 after created new client, but got {response.status_code}"
        )
        self.assertEqual(data['clientname'], 'new_client')
        self.assertEqual(data['vat'], 'vat34')
        self.assertEqual(data['brn'], 'brn_cli')
        self.assertEqual(data['nic'], 'nic_cli')
        self.assertEqual(data['email'], 'new_client-emails@gmail.com')
        self.assertEqual(data['contact'], '+230 5429 7857')


    def test_add_client_user_not_authenticated(self):
        """post data to create a new client when the user is not authenticated"""
        response = self.client.post(f"{self.client_list_url}add/", {
            "clientname": "new_client",
            "vat": "vat134",
            "brn": "brn_clie",
            "nic": "nic_cl",
            "email": "new_client-emails@gmail.com",
            "contact": "+230 5429 7857",
        }, format='json')

        # Assert that the response code is 401 if the user is not authenticated
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"Expected status code 401 if the user is not authenticated, but got {response.status_code}"
        )


    def test_add_client_unauthorized_user(self):
        """post data to create a new client when the user has not add_client permission"""
        self.client.login(username='testuser2', password='testpassword')
        response = self.client.post(f"{self.client_list_url}add/", {
            "clientname": "new_client",
            "vat": "vat14",
            "brn": "brn_12",
            "nic": "nic",
            "email": "new_client-emails@gmail.com",
            "contact": "+230 5429 7857",
        }, format='json')


        # Assert that the response code is 403 if the user is not authenticated
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            f"Expected status code 403 if the user has not the permission to add new client, "
            f"but got {response.status_code}"
        )


    def test_update_client_authenticated_user_with_permissions(self):
        # Login with the test user
        self.client.login(username='testuser', password='testpassword')
        # Make the PUT request to update the client
        client = Client.objects.first()
        response = self.client.put(f"{self.client_list_url}{client.id}/", {
            'clientname': 'updated_clientname',
            'email': client.email,
            'contact': client.contact,
        }, format='json')

        data = response.json()

        # Assert that the response code is 200 after updating the client
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            f"Expected status code 200 after updating client, but got {response.status_code}"
        )
        self.assertEqual(data['clientname'], 'updated_clientname')




