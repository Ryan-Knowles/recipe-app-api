from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
CURRENT_USER_URL = reverse('user:current_user')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Tests our publicly available user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test that creating a user with a valid payload is successful"""
        payload = {
            'email': 'bob@bobsbarricades.com',
            'password': 'getrich',
            'name': 'Builder Bob',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_duplicate_user(self):
        """Test that creating a duplicate user results in a failure"""
        payload = {
            'email': 'bob@bobsbarricades.com',
            'password': 'getrich',
            'name': 'Builder Bob',
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password is long enough"""
        payload = {
            'email': 'bob@bobsbarricades.com',
            'password': 'moo',
            'name': 'Builder Bob',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_invalid_email(self):
        """Test that creating a user with an invalid email is a failure"""
        payload = {
            'email': 'bob',
            'password': 'getrich',
            'name': 'Builder Bob',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user_is_successful(self):
        """Test that a token is successfully created for the user"""
        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
        }

        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_for_invalid_credentials_fails(self):
        """
        Test that a token is not created invalid credentials are given
        """
        create_user(email='test@test.com', password='supersecurepassword')
        payload = {
            'email': 'test@test.com',
            'password': 'ThisIsNotMyPassword',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_invalid_user(self):
        """Test that token is not created for user that doesn't exist"""
        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required to get a token"""
        payload = {
            'email': 'bademail',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_while_unauthorized_fails(self):
        """Authentication is required for users"""
        res = self.client.get(CURRENT_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Tests our private users API that requires authentication"""

    def setUp(self) -> None:
        self.user = create_user(
            email='test@test.com',
            password='SecurePassword',
            name='Tester Bob'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_user_while_authenticated_succeeds(self):
        """Test retrieving profile for logging in user"""
        res = self.client.get(CURRENT_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
        })

    def test_post_to_get_user_not_allowed(self):
        """Test that POST is not allowed on the current user url"""
        res = self.client.post(CURRENT_USER_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_succeeds(self):
        """Test that updating the user profile with valid data is successful"""
        payload = {
            'name': 'Tester Bob 2',
            'password': 'SecurePass2'
        }

        res = self.client.patch(CURRENT_USER_URL, payload)

        # Get updated values from the DB
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
