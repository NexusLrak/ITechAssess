from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Food, MealRecord

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get('class', '')

            if isinstance(widget, forms.Select):
                css = 'form-select'
            elif isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input'
            else:
                css = 'form-control'

            widget.attrs['class'] = f'{existing} {css}'.strip()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class FoodForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Food
        fields = ['name', 'unit', 'calories', 'protein', 'fat', 'carbohydrates', 'fiber']
        widgets = {
            field: forms.NumberInput(attrs={'step': '0.01'})
            for field in ['calories', 'protein', 'fat', 'carbohydrates', 'fiber']
        }

class MealRecordForm(BootstrapFormMixin, forms.ModelForm):
    record_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = MealRecord
        fields = ['food', 'meal_type', 'quantity', 'record_date', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['food'].queryset = Food.objects.filter(user=user)


