from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

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
    change_list_template = "admin/recipes/recipe/change_list.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path("import/", self.admin_site.admin_view(self.import_view), name="recipes_recipe_import"),
        ]
        return custom + urls

    def import_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        import json

        if request.method != "POST":
            return render(request, "admin/recipes/recipe/import.html", {"title": "Import Recipes"})

        upload = request.FILES.get("json_file")
        if not upload:
            messages.error(request, "No file uploaded.")
            return redirect(".")

        try:
            data = json.load(upload)
        except Exception as e:
            messages.error(request, f"Invalid JSON: {e}")
            return redirect(".")

        try:
            table = next(item for item in data if item.get("type") == "table" and item.get("name") == "recipes")
            records = table["data"]
        except StopIteration:
            messages.error(request, "No 'recipes' table found in JSON.")
            return redirect(".")

        created, skipped, errors = 0, 0, []

        for row in records:
            title = (row.get("name") or "").strip()
            if not title:
                continue

            if Recipe.objects.filter(title__iexact=title).exists():
                skipped += 1
                continue

            try:
                with transaction.atomic():
                    recipe = Recipe.objects.create(
                        title=title,
                        author=(row.get("author") or "").strip(),
                        created_by=request.user,
                    )

                    order = 0
                    for line in (row.get("ingredients") or "").splitlines():
                        line = line.strip()
                        if not line or line.startswith("*") or line.startswith("#"):
                            continue
                        ingredient, _ = Ingredient.objects.get_or_create(name=line)
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=ingredient,
                            quantity="",
                            unit="",
                            order=order,
                        )
                        order += 1

                    instructions = (row.get("instructions") or "").strip()
                    if instructions:
                        RecipeStep.objects.create(recipe=recipe, step_number=1, instruction=instructions)

                created += 1
            except Exception as e:
                errors.append(f"{title}: {e}")

        context = {
            "title": "Import Recipes — Results",
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }
        return render(request, "admin/recipes/recipe/import.html", context)


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
