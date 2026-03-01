from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import RecipeForm, RecipeIngredientFormSet, RecipeStepFormSet
from .models import Recipe


class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 20

    def get_queryset(self):
        qs = Recipe.objects.prefetch_related('tags').distinct()
        q = self.request.GET.get('q', '').strip()
        tag = self.request.GET.get('tag', '').strip()
        difficulty = self.request.GET.get('difficulty', '').strip()

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(recipe_ingredients__ingredient__name__icontains=q)
            ).distinct()
        if tag:
            qs = qs.filter(tags__slug=tag)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['tag'] = self.request.GET.get('tag', '')
        ctx['difficulty'] = self.request.GET.get('difficulty', '')
        ctx['difficulty_choices'] = Recipe.DIFFICULTY_CHOICES
        return ctx


class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'tags', 'recipe_ingredients__ingredient', 'steps'
        )


class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['ingredient_formset'] = RecipeIngredientFormSet(self.request.POST)
            ctx['step_formset'] = RecipeStepFormSet(self.request.POST, self.request.FILES)
        else:
            ctx['ingredient_formset'] = RecipeIngredientFormSet()
            ctx['step_formset'] = RecipeStepFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        ingredient_formset = ctx['ingredient_formset']
        step_formset = ctx['step_formset']

        if ingredient_formset.is_valid() and step_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            step_formset.instance = self.object
            step_formset.save()
            return super().form_valid(form)
        return self.render_to_response(ctx)

    def get_success_url(self):
        return self.object.get_absolute_url()


class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['ingredient_formset'] = RecipeIngredientFormSet(
                self.request.POST, instance=self.object
            )
            ctx['step_formset'] = RecipeStepFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            ctx['ingredient_formset'] = RecipeIngredientFormSet(instance=self.object)
            ctx['step_formset'] = RecipeStepFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        ingredient_formset = ctx['ingredient_formset']
        step_formset = ctx['step_formset']

        if ingredient_formset.is_valid() and step_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            step_formset.instance = self.object
            step_formset.save()
            return super().form_valid(form)
        return self.render_to_response(ctx)

    def get_success_url(self):
        return self.object.get_absolute_url()


class RecipeDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    context_object_name = 'recipe'
    success_url = reverse_lazy('recipes:list')
