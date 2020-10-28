from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cucumber'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **kwargs):
    """Create and return a sample recipe"""
    return Recipe.objects.create(user=user, **kwargs)


class PublicRecipeApiTests(TestCase):
    """Tests our publicly available recipe api"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Tests that login is required to retrieve recipes"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Tests our private recipe api that requires authentication"""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@vocalized.test',
            password='SecurePassword123',
            name='Tester Bob'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_recipes(self):
        """Test getting our recipes"""
        Recipe.objects.create(
            user=self.user,
            title='Test Recipe',
            time_minutes=10,
            price=10.00
        )

        Recipe.objects.create(
            user=self.user,
            title='Test Recipe 2',
            time_minutes=12,
            price=15.00
        )

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_only_recipes_for_current_user(self):
        """Test getting our recipes for current user"""
        user2 = get_user_model().objects.create_user(
            email='test2@vocalized.test',
            password='SecurePassword123',
            name='Tester Bob 2'
        )

        recipe = Recipe.objects.create(
            user=self.user,
            title='Test Recipe',
            time_minutes=10,
            price=10.00
        )

        Recipe.objects.create(
            user=user2,
            title='Test Recipe 2',
            time_minutes=12,
            price=15.00
        )

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], recipe.title)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = Recipe.objects.create(
            user=self.user,
            title='Test Recipe',
            time_minutes=10,
            price=10.00
        )

        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe without tags or ingredients"""
        payload = {
            'title': 'Chocolate Cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="Vegan")
        tag2 = sample_tag(user=self.user, name="Dessert")

        payload = {
            'title': 'Avocado Lime Cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ing1 = sample_ingredient(user=self.user, name="Prawns")
        ing2 = sample_ingredient(user=self.user, name="Garlic")

        payload = {
            'title': 'Prawns on the Barbie',
            'ingredients': [ing1.id, ing2.id],
            'time_minutes': 30,
            'price': 40.00
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ings = recipe.ingredients.all()
        self.assertEqual(ings.count(), 2)
        self.assertIn(ing1, ings)
        self.assertIn(ing2, ings)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        tag = sample_tag(
            user=self.user,
            name='Dessert'
        )
        ingred1 = sample_ingredient(
            user=self.user,
            name='Cheese'
        )
        ingred2 = sample_ingredient(
            user=self.user,
            name='Cake'
        )
        ingred3 = sample_ingredient(
            user=self.user,
            name='Sugar'
        )
        recipe = sample_recipe(
            user=self.user,
            title='Cheesecake',
            time_minutes=30,
            price=10.00
        )

        # recipe.tags.set([tag])
        recipe.tags.add(tag)
        recipe.ingredients.set([ingred1, ingred2])

        payload = {
            'title': 'Cheesecake Supreme',
            'ingredients': [ingred2.id, ingred3.id]
        }

        # You can use recipe.refresh_from_db() instead and use the same
        # recipe object
        res = self.client.patch(detail_url(recipe.id), payload)
        recipe_from_db = Recipe.objects.get(id=recipe.id)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingred1, recipe_from_db.ingredients.all())
        self.assertIn(ingred2, recipe_from_db.ingredients.all())
        self.assertIn(ingred3, recipe_from_db.ingredients.all())
        self.assertEqual(payload['title'], recipe_from_db.title)

    def test_full_update_recipe(self):
        """Test updated a recipe with put"""
        tag = sample_tag(
            user=self.user,
            name='Vegan'
        )
        tag2 = sample_tag(
            user=self.user,
            name='Non Vegan'
        )
        tag3 = sample_tag(
            user=self.user,
            name='Dessert'
        )
        ingred = sample_ingredient(
            user=self.user,
            name='Cheese'
        )
        recipe = sample_recipe(
            user=self.user,
            title='Cheesecake',
            time_minutes=60,
            price=20.00
        )

        payload = {
            'title': 'Cheesecake',
            'time_minutes': 60,
            'price': 25.00,
            'tags': [tag2.id, tag3.id],
            'ingredients': [ingred.id]
        }

        res = self.client.put(detail_url(recipe.id), payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())
        self.assertIn(tag3, recipe.tags.all())
        self.assertEqual(payload['price'], recipe.price)
