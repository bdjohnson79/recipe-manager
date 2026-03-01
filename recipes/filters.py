import django_filters

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains', label='Title contains')
    tags = django_filters.CharFilter(field_name='tags__slug', lookup_expr='exact', label='Tag slug')
    difficulty = django_filters.ChoiceFilter(choices=Recipe.DIFFICULTY_CHOICES)
    max_time = django_filters.NumberFilter(field_name='cook_time', lookup_expr='lte', label='Max cook time (min)')
    min_time = django_filters.NumberFilter(field_name='cook_time', lookup_expr='gte', label='Min cook time (min)')
    ingredient = django_filters.CharFilter(
        field_name='recipe_ingredients__ingredient__name',
        lookup_expr='icontains',
        label='Ingredient name contains',
    )

    class Meta:
        model = Recipe
        fields = ['title', 'tags', 'difficulty', 'max_time', 'min_time', 'ingredient']
