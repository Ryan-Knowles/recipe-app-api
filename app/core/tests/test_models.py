from django.test import TestCase
from django.contrib.auth import get_user_model


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


  def test_new_user_with_invalid_email(self):
    """
    Test creating a new user with an invalid email and ensure an error is raised
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

    