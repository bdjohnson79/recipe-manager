from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag

User = get_user_model()


def make_recipe(**kwargs):
    defaults = {'title': 'Test Recipe', 'prep_time': 5, 'cook_time': 10, 'difficulty': 'easy'}
    defaults.update(kwargs)
    return Recipe.objects.create(**defaults)


def make_approved_user(**kwargs):
    defaults = {'username': 'testuser', 'password': 'pass'}
    defaults.update(kwargs)
    user = User.objects.create_user(**defaults)
    user.profile.is_approved = True
    user.profile.save()
    return user


class RecipeListViewTest(TestCase):
    def setUp(self):
        self.url = reverse('recipes:list')
        self.r1 = make_recipe(title='Spaghetti', difficulty='easy')
        self.r2 = make_recipe(title='Risotto', difficulty='hard')

    def test_list_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Spaghetti')
        self.assertContains(response, 'Risotto')

    def test_search_by_title(self):
        response = self.client.get(self.url, {'q': 'Spaghetti'})
        self.assertContains(response, 'Spaghetti')
        self.assertNotContains(response, 'Risotto')

    def test_filter_by_difficulty(self):
        response = self.client.get(self.url, {'difficulty': 'hard'})
        self.assertContains(response, 'Risotto')
        self.assertNotContains(response, 'Spaghetti')

    def test_filter_by_tag(self):
        tag = Tag.objects.create(name='Italian', slug='italian')
        self.r1.tags.add(tag)
        response = self.client.get(self.url, {'tag': 'italian'})
        self.assertContains(response, 'Spaghetti')
        self.assertNotContains(response, 'Risotto')


class RecipeDetailViewTest(TestCase):
    def setUp(self):
        self.recipe = make_recipe(title='Tacos', description='Delicious tacos')
        self.url = reverse('recipes:detail', kwargs={'slug': self.recipe.slug})

    def test_detail_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tacos')
        self.assertContains(response, 'Delicious tacos')

    def test_404_for_invalid_slug(self):
        response = self.client.get(reverse('recipes:detail', kwargs={'slug': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)


class RecipeCreateViewTest(TestCase):
    def setUp(self):
        self.url = reverse('recipes:create')
        self.user = make_approved_user()
        self.client.force_login(self.user)

    def test_get_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    def test_post_creates_recipe(self):
        data = {
            'title': 'New Recipe',
            'description': 'A test recipe',
            'servings': 2,
            'prep_time': 10,
            'cook_time': 20,
            'difficulty': 'easy',
            # Ingredient formset management form
            'recipe_ingredients-TOTAL_FORMS': '0',
            'recipe_ingredients-INITIAL_FORMS': '0',
            'recipe_ingredients-MIN_NUM_FORMS': '0',
            'recipe_ingredients-MAX_NUM_FORMS': '1000',
            # Step formset management form
            'steps-TOTAL_FORMS': '0',
            'steps-INITIAL_FORMS': '0',
            'steps-MIN_NUM_FORMS': '0',
            'steps-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(Recipe.objects.filter(title='New Recipe').count(), 1)
        recipe = Recipe.objects.get(title='New Recipe')
        self.assertRedirects(response, recipe.get_absolute_url())

    def test_unapproved_user_redirected(self):
        unapproved = User.objects.create_user(username='unapproved', password='pass')
        self.client.force_login(unapproved)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('recipes:list'))

    def test_unapproved_user_sees_warning(self):
        unapproved = User.objects.create_user(username='unapproved', password='pass')
        self.client.force_login(unapproved)
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, 'pending admin approval')


class RecipeUpdateViewTest(TestCase):
    def setUp(self):
        self.user = make_approved_user()
        self.client.force_login(self.user)
        self.recipe = make_recipe(title='Old Title')
        self.url = reverse('recipes:edit', kwargs={'slug': self.recipe.slug})

    def test_get_edit_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_approved_user_can_edit_any_recipe(self):
        other = make_approved_user(username='other')
        recipe = make_recipe(title='Someone Elses Recipe', created_by=other)
        url = reverse('recipes:edit', kwargs={'slug': recipe.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_updates_recipe(self):
        data = {
            'title': 'Updated Title',
            'description': '',
            'servings': 1,
            'prep_time': 5,
            'cook_time': 10,
            'difficulty': 'medium',
            'recipe_ingredients-TOTAL_FORMS': '0',
            'recipe_ingredients-INITIAL_FORMS': '0',
            'recipe_ingredients-MIN_NUM_FORMS': '0',
            'recipe_ingredients-MAX_NUM_FORMS': '1000',
            'steps-TOTAL_FORMS': '0',
            'steps-INITIAL_FORMS': '0',
            'steps-MIN_NUM_FORMS': '0',
            'steps-MAX_NUM_FORMS': '1000',
        }
        self.client.post(self.url, data)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, 'Updated Title')

    def test_unapproved_user_redirected(self):
        unapproved = User.objects.create_user(username='unapproved', password='pass')
        self.client.force_login(unapproved)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('recipes:list'))


class RecipeDeleteViewTest(TestCase):
    def setUp(self):
        self.user = make_approved_user()
        self.client.force_login(self.user)
        self.recipe = make_recipe(title='To Delete')
        self.url = reverse('recipes:delete', kwargs={'slug': self.recipe.slug})

    def test_get_confirm_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'To Delete')

    def test_post_deletes_recipe(self):
        self.client.post(self.url)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_unapproved_user_redirected(self):
        unapproved = User.objects.create_user(username='unapproved', password='pass')
        self.client.force_login(unapproved)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('recipes:list'))


class AuthPageStylingTest(TestCase):
    """Verify that allauth auth pages use our custom base.html (not allauth's defaults)."""

    NAV_BRAND = 'Recipe Manager'  # present in base.html nav, absent from allauth defaults

    def test_login_page_uses_base_template(self):
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)

    def test_signup_page_uses_base_template(self):
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)

    def test_logout_page_uses_base_template(self):
        user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(user)
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)

    def test_social_login_page_uses_base_template(self):
        response = self.client.get(reverse('google_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)

    def test_social_login_cancelled_page_uses_base_template(self):
        response = self.client.get(reverse('socialaccount_login_cancelled'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)

    def test_social_auth_error_page_uses_base_template(self):
        response = self.client.get(reverse('socialaccount_login_error'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.NAV_BRAND)
