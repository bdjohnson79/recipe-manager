from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag


def make_recipe(**kwargs):
    defaults = {'title': 'API Recipe', 'prep_time': 5, 'cook_time': 15, 'difficulty': 'easy'}
    defaults.update(kwargs)
    return Recipe.objects.create(**defaults)


class RecipeAPIListTest(APITestCase):
    def setUp(self):
        self.url = '/recipes/api/recipes/'
        self.r1 = make_recipe(title='Pizza')
        self.r2 = make_recipe(title='Soup')

    def test_list_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_contains_recipes(self):
        response = self.client.get(self.url)
        titles = [r['title'] for r in response.data['results']]
        self.assertIn('Pizza', titles)
        self.assertIn('Soup', titles)

    def test_search(self):
        response = self.client.get(self.url, {'search': 'Pizza'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [r['title'] for r in response.data['results']]
        self.assertIn('Pizza', titles)

    def test_filter_by_difficulty(self):
        make_recipe(title='Hard Dish', difficulty='hard')
        response = self.client.get(self.url, {'difficulty': 'hard'})
        titles = [r['title'] for r in response.data['results']]
        self.assertIn('Hard Dish', titles)
        self.assertNotIn('Pizza', titles)


class RecipeAPIDetailTest(APITestCase):
    def setUp(self):
        self.recipe = make_recipe(title='Steak')
        self.url = f'/recipes/api/recipes/{self.recipe.pk}/'

    def test_retrieve(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Steak')

    def test_update(self):
        response = self.client.patch(self.url, {'title': 'Grilled Steak'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Grilled Steak')

    def test_delete(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())


class RecipeAPICreateTest(APITestCase):
    def setUp(self):
        self.url = '/recipes/api/recipes/'

    def test_create_recipe(self):
        data = {
            'title': 'New API Recipe',
            'prep_time': 10,
            'cook_time': 30,
            'difficulty': 'medium',
            'servings': 4,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Recipe.objects.filter(title='New API Recipe').exists())


class TagAPITest(APITestCase):
    def setUp(self):
        self.url = '/recipes/api/tags/'

    def test_list(self):
        Tag.objects.create(name='Vegan', slug='vegan')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self):
        response = self.client.post(self.url, {'name': 'Gluten Free', 'slug': 'gluten-free'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class IngredientAPITest(APITestCase):
    def setUp(self):
        self.url = '/recipes/api/ingredients/'

    def test_list(self):
        Ingredient.objects.create(name='Flour')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search(self):
        Ingredient.objects.create(name='Olive Oil')
        response = self.client.get(self.url, {'search': 'olive'})
        names = [i['name'] for i in response.data['results']]
        self.assertIn('Olive Oil', names)
