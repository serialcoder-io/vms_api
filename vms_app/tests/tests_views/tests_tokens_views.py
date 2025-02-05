# from django.contrib.auth.models import Permission
# from django.db.models import Max
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from vms_app.models import User

class TokenViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='usertest', password='testpassword')
        self.client = APIClient()
        self.token_obtain_url = "/vms/auth/token/"
        self.token_refresh_url = "/vms/auth/token/refresh/"
        self.token_verify_url = "/vms/auth/token/verify/"

    def test_obtain_token_pair(self):
        """Test obtaining JWT pair (access and refresh tokens)"""
        response = self.client.post(self.token_obtain_url, {
            'username': 'usertest',
            'password': 'testpassword'
        })
        data = response.json()

        # Check if the response has both access and refresh tokens
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', data)
        self.assertIn('refresh', data)

        # Store tokens for further testing
        self.access_token = data['access']
        self.refresh_token = data['refresh']

    def test_obtain_token_invalid_credentials(self):
        """Test obtaining token with invalid credentials"""
        response = self.client.post(self.token_obtain_url, {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        # Should return 401 Unauthorized
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"Should return 401 Unauthorized but got {response.status_code}"
        )

    def test_refresh_token(self):
        """Test refreshing the JWT access token"""
        # obtain the token pair
        response = self.client.post(self.token_obtain_url, {
            'username': 'usertest',
            'password': 'testpassword'
        })
        refresh_token = response.json().get('refresh')

        # Now use the refresh token to get a new access token
        response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })
        data = response.json()

        # Check if the response has a new access token
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', data)

    def test_verify_token(self):
        """Test verifying the validity of a JWT access token"""
        # obtain the token pair
        response = self.client.post(self.token_obtain_url, {
            'username': 'usertest',
            'password': 'testpassword'
        })
        access_token = response.json().get('access')

        response = self.client.post(self.token_verify_url, {
            'token': access_token
        })

        # Check if the token is valid (status code 200 OK)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK,
            f"token should be valid if credentials are corerct: "
            f"status 200, but got {response.status_code}"
        )

    def test_verify_invalid_token(self):
        """Test verifying an invalid JWT access token"""
        # Try to verify a random invalid token
        response = self.client.post(self.token_verify_url, {
            'token': 'invalidtoken123'
        })

        # Check if the token is invalid (status code 401 Unauthorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            f"status must be 401, but got {response.status_code}"
        )

    def test_blacklist_after_rotation(self):
        """Test that old refresh tokens are blacklisted after rotation"""
        # obtain the token pair
        response = self.client.post(self.token_obtain_url, {
            'username': 'usertest',
            'password': 'testpassword'
        })
        refresh_token = response.json().get('refresh')

        # Use the refresh token to get new access and refresh tokens
        response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })
        new_refresh_token = response.json().get('refresh')

        # use the old refresh token (which should be blacklisted)
        response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })

        # Check if the old refresh token is blacklisted (status 401 Unauthorized)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "old refresh tokens should be blacklisted after rotation"
        )
        self.assertEqual(
            'token_not_valid',
                 response.json()["code"],
            "response must contain key(code) with value 'token_not_valid'"
        )

        #verify the new refresh token still works
        response = self.client.post(self.token_refresh_url, {
            'refresh': new_refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)