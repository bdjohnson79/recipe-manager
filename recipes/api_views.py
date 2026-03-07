from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS

from django_filters.rest_framework import DjangoFilterBackend

from .filters import RecipeFilter
from .models import Ingredient, Recipe, Tag
from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    TagSerializer,
)


class IsApprovedUserOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method not in SAFE_METHODS:
            profile = getattr(request.user, 'profile', None)
            return bool(profile and profile.is_approved)
        return True


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedUserOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RecipeFilter
    search_fields = ['title', 'description', 'recipe_ingredients__ingredient__name']
    ordering_fields = ['created_at', 'cook_time', 'prep_time', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Recipe.objects.prefetch_related(
            'tags', 'recipe_ingredients__ingredient', 'steps'
        ).distinct()
        if self.action in ('update', 'partial_update', 'destroy'):
            qs = qs.filter(author=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeListSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedUserOrReadOnly]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedUserOrReadOnly]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']
