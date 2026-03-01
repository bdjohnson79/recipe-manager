from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'prep_time', 'cook_time', 'servings', 'created_at']
    list_filter = ['difficulty', 'tags']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    inlines = [RecipeIngredientInline, RecipeStepInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'unit', 'order']
    list_filter = ['recipe']


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'step_number', 'instruction']
    list_filter = ['recipe']
