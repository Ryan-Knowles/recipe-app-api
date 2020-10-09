from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Tests our publicly available ingredients API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Tests our private ingredients API that requires authentication"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@vocalized.test',
            password='SecurePassword123',
            name='Tester Bob'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(
            user=self.user,
            name='Beef'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Ham'
        )

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients retrieved are only for the
        authenticated user"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Beef'
        )

        user2 = get_user_model().objects.create_user(
            email='test2@vocalized.test',
            password='TestPass123',
            name='Tester Fred'
        )

        Ingredient.objects.create(
            user=user2,
            name='Fish'
        )

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_succeeds(self):
        """Test creating a new ingredient"""
        payload = {
            'name': 'Test Ingredient'
        }
        res = self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_invalid_ingredient_fails(self):
        """Test creating a new ingredient with invalid payload fails"""
        payload = {
            'name': ''
        }
        res = self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(exists)
