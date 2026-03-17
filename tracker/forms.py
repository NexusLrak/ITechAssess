from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import get_user_model

from .models import *

User = get_user_model()

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
            'calories': forms.NumberInput(attrs={'step': '0.01', 'readonly': 'readonly'}),
            'protein': forms.NumberInput(attrs={'step': '0.01'}),
            'fat': forms.NumberInput(attrs={'step': '0.01'}),
            'carbohydrates': forms.NumberInput(attrs={'step': '0.01'}),
            'fiber': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        protein = cleaned_data.get('protein')
        carbohydrates = cleaned_data.get('carbohydrates')
        fat = cleaned_data.get('fat')
        fiber = cleaned_data.get('fiber')

        if None not in (protein, carbohydrates, fat, fiber):
            calories = 4.0 * protein + 4.0 * carbohydrates + 9.0 * fat + 2.0 * fiber
            cleaned_data['calories'] = round(calories, 2)

        return cleaned_data
    
class StyledFormMixin:
    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} form-control".strip()


class ProfileUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class CustomPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["old_password"].label = "Current Password"
        self.fields["new_password1"].label = "New Password"
        self.fields["new_password2"].label = "Confirm New Password"


class DeleteAccountForm(StyledFormMixin, forms.Form):
    password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(),
    )
    confirm_text = forms.CharField(
        label="Type DELETE to confirm",
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.apply_bootstrap_classes()

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password

    def clean_confirm_text(self):
        confirm_text = self.cleaned_data["confirm_text"]
        if confirm_text != "DELETE":
            raise forms.ValidationError('Please type "DELETE" exactly.')
        return confirm_text
    
from django.db.models import Q
class MealRecordForm(BootstrapFormMixin, forms.ModelForm):
    food = forms.ModelChoiceField(
        queryset=Food.objects.none(),
        label='Food'
    )

    class Meta:
        model = MealRecord
        fields = ['food', 'meal_type', 'quantity', 'record_date', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'record_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user is not None:
            admin_user = User.objects.filter(is_superuser=True).first()
            self.fields['food'].queryset = Food.objects.filter(Q(user=self.user) | Q(user=admin_user))

    def save(self, commit=True):
        if self.user is None:
            raise ValueError('MealRecordForm.save() requires user')

        food = self.cleaned_data['food']

        instance = super().save(commit=False)
        instance.user = self.user

        instance.food_name = food.name
        instance.food_unit = food.unit
        instance.food_calories = food.calories
        instance.food_protein = food.protein
        instance.food_fat = food.fat
        instance.food_carbohydrates = food.carbohydrates
        instance.food_fiber = food.fiber

        if commit:
            instance.save()

        return instance