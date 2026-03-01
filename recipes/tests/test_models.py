from django.test import TestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag


class TagModelTest(TestCase):
    def test_slug_auto_generated(self):
        tag = Tag.objects.create(name='Quick Meals')
        self.assertEqual(tag.slug, 'quick-meals')

    def test_str(self):
        tag = Tag(name='Vegan')
        self.assertEqual(str(tag), 'Vegan')


class RecipeModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title='Pasta Carbonara',
            prep_time=10,
            cook_time=20,
            servings=2,
            difficulty='easy',
        )

    def test_slug_auto_generated(self):
        self.assertEqual(self.recipe.slug, 'pasta-carbonara')

    def test_total_time(self):
        self.assertEqual(self.recipe.total_time, 30)

    def test_str(self):
        self.assertEqual(str(self.recipe), 'Pasta Carbonara')

    def test_slug_uniqueness(self):
        recipe2 = Recipe.objects.create(title='Pasta Carbonara', prep_time=5, cook_time=15)
        self.assertNotEqual(recipe2.slug, self.recipe.slug)
        self.assertTrue(recipe2.slug.startswith('pasta-carbonara-'))

    def test_get_absolute_url(self):
        url = self.recipe.get_absolute_url()
        self.assertIn(self.recipe.slug, url)


class RecipeIngredientModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(title='Test Recipe', prep_time=5, cook_time=10)
        self.ingredient = Ingredient.objects.create(name='Salt')

    def test_create_recipe_ingredient(self):
        ri = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            quantity='1',
            unit='tsp',
        )
        self.assertEqual(ri.recipe, self.recipe)
        self.assertEqual(ri.ingredient.name, 'Salt')

    def test_str(self):
        ri = RecipeIngredient(
            ingredient=self.ingredient, quantity='2', unit='cups'
        )
        self.assertIn('Salt', str(ri))


class RecipeStepModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(title='Test Recipe', prep_time=5, cook_time=10)

    def test_create_step(self):
        step = RecipeStep.objects.create(
            recipe=self.recipe,
            step_number=1,
            instruction='Boil water.',
        )
        self.assertEqual(step.step_number, 1)

    def test_unique_together(self):
        RecipeStep.objects.create(recipe=self.recipe, step_number=1, instruction='Step 1')
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            RecipeStep.objects.create(recipe=self.recipe, step_number=1, instruction='Duplicate')
