from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    servings = models.PositiveSmallIntegerField(default=1)
    prep_time = models.PositiveIntegerField(help_text='Prep time in minutes', default=0)
    cook_time = models.PositiveIntegerField(help_text='Cook time in minutes', default=0)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='recipes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Recipe.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def total_time(self):
        return self.prep_time + self.cook_time

    def get_absolute_url(self):
        return reverse('recipes:detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='recipe_ingredients')
    quantity = models.CharField(max_length=50)
    unit = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.quantity} {self.unit} {self.ingredient.name}'.strip()


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveSmallIntegerField()
    instruction = models.TextField()
    image = models.ImageField(upload_to='steps/', blank=True, null=True)

    class Meta:
        ordering = ['step_number']
        unique_together = [('recipe', 'step_number')]

    def __str__(self):
        return f'Step {self.step_number}: {self.instruction[:50]}'
