from django.test import TestCase

from recipes.filters import RecipeFilter
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


def make_recipe(**kwargs):
    defaults = {'title': 'Filter Recipe', 'prep_time': 5, 'cook_time': 20, 'difficulty': 'easy'}
    defaults.update(kwargs)
    return Recipe.objects.create(**defaults)


class RecipeFilterTest(TestCase):
    def setUp(self):
        self.italian = Tag.objects.create(name='Italian', slug='italian')
        self.vegan = Tag.objects.create(name='Vegan', slug='vegan')

        self.r1 = make_recipe(title='Carbonara', difficulty='hard', cook_time=30)
        self.r1.tags.add(self.italian)

        self.r2 = make_recipe(title='Lentil Soup', difficulty='easy', cook_time=45)
        self.r2.tags.add(self.vegan)

        self.r3 = make_recipe(title='Risotto', difficulty='medium', cook_time=20)
        self.r3.tags.add(self.italian)

        self.ingredient = Ingredient.objects.create(name='Pancetta')
        RecipeIngredient.objects.create(
            recipe=self.r1, ingredient=self.ingredient, quantity='100', unit='g'
        )

    def test_filter_by_title(self):
        f = RecipeFilter({'title': 'carb'}, queryset=Recipe.objects.all())
        self.assertIn(self.r1, f.qs)
        self.assertNotIn(self.r2, f.qs)

    def test_filter_by_difficulty(self):
        f = RecipeFilter({'difficulty': 'hard'}, queryset=Recipe.objects.all())
        self.assertIn(self.r1, f.qs)
        self.assertNotIn(self.r2, f.qs)

    def test_filter_by_tag_slug(self):
        f = RecipeFilter({'tags': 'italian'}, queryset=Recipe.objects.all())
        self.assertIn(self.r1, f.qs)
        self.assertIn(self.r3, f.qs)
        self.assertNotIn(self.r2, f.qs)

    def test_filter_max_time(self):
        f = RecipeFilter({'max_time': 25}, queryset=Recipe.objects.all())
        self.assertIn(self.r3, f.qs)  # cook_time=20
        self.assertNotIn(self.r1, f.qs)  # cook_time=30
        self.assertNotIn(self.r2, f.qs)  # cook_time=45

    def test_filter_min_time(self):
        f = RecipeFilter({'min_time': 30}, queryset=Recipe.objects.all())
        self.assertIn(self.r1, f.qs)  # cook_time=30
        self.assertIn(self.r2, f.qs)  # cook_time=45
        self.assertNotIn(self.r3, f.qs)  # cook_time=20

    def test_filter_by_ingredient(self):
        f = RecipeFilter({'ingredient': 'pancetta'}, queryset=Recipe.objects.all())
        self.assertIn(self.r1, f.qs)
        self.assertNotIn(self.r2, f.qs)

    def test_no_filter_returns_all(self):
        f = RecipeFilter({}, queryset=Recipe.objects.all())
        self.assertEqual(f.qs.count(), 3)
