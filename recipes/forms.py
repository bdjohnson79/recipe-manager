import re

from django import forms
from django.forms import inlineformset_factory

from .models import Ingredient, Recipe, RecipeIngredient, RecipeStep


# ── Natural-language duration helpers ────────────────────────────────────────

def parse_duration(value):
    """
    Parse a natural-language duration string into whole minutes.

    Accepts, e.g.:
      "30"  "30m"  "30 minutes"
      "1h"  "1 hour"  "1 hour 30 minutes"  "1.5 hours"
      "1:30"
    Returns an int (minutes).  Raises ValueError on parse failure.
    """
    value = str(value).strip().lower()

    # bare integer → minutes
    if re.fullmatch(r'\d+', value):
        return int(value)

    # H:MM or HH:MM
    m = re.fullmatch(r'(\d+):(\d{2})', value)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    total = 0.0
    found = False

    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b', value)
    if m:
        total += float(m.group(1)) * 60
        found = True

    m = re.search(r'(\d+)\s*(?:minutes?|mins?|m)\b', value)
    if m:
        total += int(m.group(1))
        found = True

    if found:
        return int(round(total))

    raise ValueError(f"Cannot parse '{value}' as a duration.")


def minutes_to_natural(minutes):
    """Convert an integer number of minutes to a human-readable string."""
    minutes = int(minutes)
    if minutes <= 0:
        return ''
    hours, mins = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    return ' '.join(parts)


class NaturalDurationField(forms.Field):
    """A text field that accepts natural-language durations and stores minutes."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('help_text', 'e.g. "30 minutes", "1 hour 30 minutes", "1h 15m"')
        super().__init__(*args, **kwargs)
        self.widget = forms.TextInput(attrs={
            'placeholder': 'e.g. 30 minutes, 1 hour 30 minutes',
        })

    def prepare_value(self, value):
        """Convert stored integer minutes back to a readable string for display."""
        if value is None or value == '':
            return ''
        try:
            return minutes_to_natural(int(value))
        except (ValueError, TypeError):
            return value  # already a string (re-render after failed validation)

    def to_python(self, value):
        if not value or str(value).strip() == '':
            return 0
        try:
            result = parse_duration(str(value))
            if result < 0:
                raise forms.ValidationError('Time cannot be negative.')
            return result
        except ValueError:
            raise forms.ValidationError(
                'Enter a time like "30 minutes", "1 hour 30 minutes", or "1:30".'
            )


class RecipeForm(forms.ModelForm):
    prep_time = NaturalDurationField(label='Prep time')
    cook_time = NaturalDurationField(label='Cook time')

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'servings', 'prep_time', 'cook_time', 'difficulty', 'image', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.CheckboxSelectMultiple(),
        }


class RecipeIngredientForm(forms.ModelForm):
    ingredient_name = forms.CharField(max_length=100, label='Ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient_name', 'quantity', 'unit', 'notes', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.ingredient_id:
            self.fields['ingredient_name'].initial = self.instance.ingredient.name

    def save(self, commit=True):
        ingredient_name = self.cleaned_data.pop('ingredient_name', '').strip()
        instance = super().save(commit=False)
        if ingredient_name:
            ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)
            instance.ingredient = ingredient
        if commit:
            instance.save()
        return instance


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = ['step_number', 'instruction', 'image']
        widgets = {
            'instruction': forms.Textarea(attrs={'rows': 3}),
        }


RecipeIngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    extra=1,
    can_delete=True,
)

RecipeStepFormSet = inlineformset_factory(
    Recipe,
    RecipeStep,
    form=RecipeStepForm,
    extra=1,
    can_delete=True,
)
