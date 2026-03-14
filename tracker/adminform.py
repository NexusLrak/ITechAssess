from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()

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
    password = forms.CharField(label="Current Password", widget=forms.PasswordInput())
    confirm_text = forms.CharField(label='Type DELETE to confirm')

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


class AdminUserUpdateForm(StyledFormMixin, forms.ModelForm):
    is_active = forms.BooleanField(required=False)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "is_active", "is_staff", "is_superuser"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()
        for name in ["is_active", "is_staff", "is_superuser"]:
            self.fields[name].widget.attrs["class"] = "form-check-input"

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