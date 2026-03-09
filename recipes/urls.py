from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views, views

app_name = 'recipes'

router = DefaultRouter()
router.register(r'recipes', api_views.RecipeViewSet, basename='recipe')
router.register(r'tags', api_views.TagViewSet, basename='tag')
router.register(r'ingredients', api_views.IngredientViewSet, basename='ingredient')

urlpatterns = [
    # Template views
    path('', views.RecipeListView.as_view(), name='list'),
    path('create/', views.RecipeCreateView.as_view(), name='create'),
    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/create-ajax/', views.tag_create_ajax, name='tag_create_ajax'),
    path('<slug:slug>/', views.RecipeDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.RecipeUpdateView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.RecipeDeleteView.as_view(), name='delete'),
    # API
    path('api/', include(router.urls)),
]
