from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import RecipeForm, RecipeIngredientFormSet, RecipeStepFormSet, TagForm
from .models import Recipe, Tag


class ApprovedUserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_staff:
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        profile = getattr(request.user, 'profile', None)
        if not (profile and profile.is_approved):
            messages.warning(
                request,
                'Your account is pending admin approval. '
                'You can browse recipes but cannot make changes.'
            )
            return redirect('recipes:list')
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 20

    def get_queryset(self):
        qs = Recipe.objects.prefetch_related('tags').distinct().order_by('title')
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


class RecipeCreateView(ApprovedUserRequiredMixin, CreateView):
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
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            form.save_m2m()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            step_formset.instance = self.object
            step_formset.save()
            return redirect(self.get_success_url())
        messages.error(self.request, "Please correct the errors below before saving.")
        return self.render_to_response(ctx)

    def get_success_url(self):
        return self.object.get_absolute_url()


class RecipeUpdateView(ApprovedUserRequiredMixin, UpdateView):
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
            return redirect(self.get_success_url())
        messages.error(self.request, "Please correct the errors below before saving.")
        return self.render_to_response(ctx)

    def get_success_url(self):
        return self.object.get_absolute_url()


class TagListView(ListView):
    model = Tag
    template_name = 'recipes/tag_list.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return Tag.objects.annotate(recipe_count=Count('recipes')).order_by('name')

    def _user_can_create(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        return getattr(getattr(user, 'profile', None), 'is_approved', False)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self._user_can_create():
            ctx['tag_form'] = ctx.get('tag_form', TagForm())
        return ctx

    def post(self, request, *args, **kwargs):
        if not self._user_can_create():
            messages.error(request, "You don't have permission to create tags.")
            return redirect('recipes:tags')
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tag \"{form.cleaned_data['name']}\" created.")
            return redirect('recipes:tags')
        self.object_list = self.get_queryset()
        ctx = self.get_context_data(tag_form=form)
        return self.render_to_response(ctx)


class RecipeDeleteView(ApprovedUserRequiredMixin, DeleteView):
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    context_object_name = 'recipe'
    success_url = reverse_lazy('recipes:list')


@require_POST
def tag_create_ajax(request):
    user = request.user
    is_approved = (
        user.is_authenticated and (
            user.is_staff or
            getattr(getattr(user, 'profile', None), 'is_approved', False)
        )
    )
    if not is_approved:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)
    tag, _ = Tag.objects.get_or_create(name=name)
    return JsonResponse({'id': tag.pk, 'name': tag.name})
