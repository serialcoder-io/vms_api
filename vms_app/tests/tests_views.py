from django.contrib.auth.models import Permission
from django.db.models import Max
from django.test import TestCase
from rest_framework.test import APIClient
from vms_app.models import User, Client

class ClientTestCase(TestCase):
    def setUp(self):
        # Create a test user
        user1 = User.objects.create_user(username='testuser', password='testpassword')
        # create user with no permission
        user2 = User.objects.create_user(username='testuser2', password='testpassword')

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
            firstname="client1_firstname",
            lastname="client1_lastname",
            email="client1-email@gmail.com",
            contact="+230 5429 7857",
        )
        # Initialize API client for testing
        self.client = APIClient()


    def test_client_list(self):
        # Log in with the test user
        self.client.login(username='testuser', password='testpassword')
        # Make a GET request to the client list endpoint
        response = self.client.get('/vms_api/clients/')
        # Check that the response status code is 200 (OK)
        self.assertEqual(
            response.status_code, 200,
            "Expected status code 200, but got {0}".format(response.status_code)
        )


    def test_client_list_unauthenticated(self):
        # Make a GET request to the client list endpoint without authentication
        response = self.client.get('/vms_api/clients/')

        # Check that the response status code is 401 (Unauthorized)
        self.assertEqual(
            response.status_code, 401,
            "Expected status code 401, but got {0}".format(response.status_code)
        )

    def test_crud_client_authenticated(self):
        # Login with the test user
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post('/vms_api/clients/add/', {
            'firstname': 'testclient_firstname',
            'lastname': 'testclient_lastname',
            'email': 'testclient_email@gmail.com',
            'contact': '+230 5429 7857',
        }, format='json')
        data = response.json()
        # Assert that the response code is 201 after created new user
        self.assertEqual(
            response.status_code, 201,
            f"Expected status code 201 after created new client, but got {response.status_code}"
        )
        self.assertEqual(data['firstname'], 'testclient_firstname')
        self.assertEqual(data['lastname'], 'testclient_lastname')
        self.assertEqual(data['email'], 'testclient_email@gmail.com')
        self.assertEqual(data['contact'], '+230 5429 7857')


    def test_add_client_not_authenticated(self):
        """post data to create new client when the user is not authenticated"""
        response = self.client.post('/vms_api/clients/add/', {
            'firstname': 'testclient_firstname',
            'lastname': 'testclient_lastname',
            'email': 'testclient_email@gmail.com',
            'contact': '+230 5429 7857',
        }, format='json')

        data = response.json()
        # Assert that the response code is 401 is the user is not authenticated
        self.assertEqual(
            response.status_code,
            401,
            f"Expected status code 401 if the user is not authenticated, but got {response.status_code}"
        )


    def test_crud_client_unauthorize(self):
        """post data to create new client when the user has not add_client permission"""
        self.client.login(username='testuser2', password='testpassword')
        response = self.client.post('/vms_api/clients/add/', {
            'firstname': 'testclient_firstname',
            'lastname': 'testclient_lastname',
            'email': 'testclient_email@gmail.com',
            'contact': '+230 5429 7857',
        }, format='json')

        data = response.json()
        # Assert that the response code is 401 is the user is not authenticated
        self.assertEqual(
            response.status_code,
            403,
            f"Expected status code 403 if the user has not the permission to add new client, "
            f"but got {response.status_code}"
        )





