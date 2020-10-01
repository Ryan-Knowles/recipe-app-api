from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Tests to our public user API that doesn't require authentication"""

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


class PrivateUserApiTests(TestCase):
    """Tests to our private users API that requires authentication"""
