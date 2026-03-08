from rest_framework import serializers

from .models import Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient_name', 'quantity', 'unit', 'notes', 'order']


class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ['id', 'step_number', 'instruction']


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    total_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'slug', 'author', 'source_url', 'description', 'servings',
            'prep_time', 'cook_time', 'total_time', 'difficulty',
            'image', 'tags', 'created_at', 'updated_at',
        ]


class RecipeDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True, source='tags', required=False
    )
    recipe_ingredients = RecipeIngredientSerializer(many=True, required=False)
    steps = RecipeStepSerializer(many=True, required=False)
    total_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'slug', 'author', 'source_url', 'description', 'servings',
            'prep_time', 'cook_time', 'total_time', 'difficulty',
            'image', 'tags', 'tag_ids', 'recipe_ingredients', 'steps',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def _save_ingredients(self, recipe, ingredients_data):
        recipe.recipe_ingredients.all().delete()
        for item in ingredients_data:
            ingredient_data = item.pop('ingredient', {})
            ingredient_name = ingredient_data.get('name', '')
            if ingredient_name:
                ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, **item)

    def _save_steps(self, recipe, steps_data):
        recipe.steps.all().delete()
        for step_data in steps_data:
            RecipeStep.objects.create(recipe=recipe, **step_data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        steps_data = validated_data.pop('steps', [])
        tags = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients_data)
        self._save_steps(recipe, steps_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        steps_data = validated_data.pop('steps', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            self._save_ingredients(instance, ingredients_data)
        if steps_data is not None:
            self._save_steps(instance, steps_data)
        return instance
