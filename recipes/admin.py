from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag, UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('is_approved',)


def approve_users(modeladmin, request, queryset):
    for user in queryset:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_approved = True
        profile.save()
    modeladmin.message_user(request, f'{queryset.count()} user(s) approved.')
approve_users.short_description = 'Approve selected users'


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'is_approved_display', 'is_staff', 'date_joined']
    list_filter = ['profile__is_approved', 'is_staff']
    actions = [approve_users]

    def is_approved_display(self, obj):
        return getattr(getattr(obj, 'profile', None), 'is_approved', False)
    is_approved_display.boolean = True
    is_approved_display.short_description = 'Approved'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
