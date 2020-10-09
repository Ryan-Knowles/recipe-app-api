from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@vocalized.ai', password='testpass', name='Tester'):
    """Create a sample user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password,
        name=name
    )


class ModelTests(TestCase):
    def test_create_user_with_email_is_successful(self):
        """
        Test where creating a new user with an email is successful
        """

        email = 'test@mooshop.com'
        password = 'SuperSecurePassword123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_with_email_normalized(self):
        """
        Test creating a new user and ensuring the email is normalized
        """
        email = 'test@MooShop.Com'
        password = 'SuperSecurePassword123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_with_invalid_email_fails(self):
        """
        Test creating a new user with an invalid email and ensure an error is
        raised
        """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'Test123')

    def test_create_new_superuser_is_successful(self):
        """
        Test creating a new superuser is successful
        """

        email = 'test@foo.com'
        password = 'test123'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_string(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_string(self):
        """Test the ingredient string representation"""
        tag = models.Ingredient.objects.create(
            user=sample_user(),
            name='Cactus Juice'
        )

        self.assertEqual(str(tag), tag.name)
