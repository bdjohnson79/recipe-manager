from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from django_filters.rest_framework import DjangoFilterBackend

from .filters import RecipeFilter
from .models import Ingredient, Recipe, Tag
from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    TagSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('tags', 'recipe_ingredients__ingredient', 'steps').distinct()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RecipeFilter
    search_fields = ['title', 'description', 'recipe_ingredients__ingredient__name']
    ordering_fields = ['created_at', 'cook_time', 'prep_time', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeListSerializer
        return RecipeDetailSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']
