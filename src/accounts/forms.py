from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, strip=False)

    class Meta:
        model = User
        fields = ["email", "name"]

    def clean_email(self):
        email = User.objects.normalize_email((self.cleaned_data.get("email") or "").strip())
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists. Sign in instead."
            )
        return email

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("A name is required.")
        if len(name) > 150:
            raise forms.ValidationError("The name must be 150 characters or fewer.")
        return name

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        if not password:
            raise forms.ValidationError("A password is required.")
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = User.objects.normalize_email(self.cleaned_data["email"])
        user.name = self.cleaned_data["name"]
        user.set_password(self.cleaned_data["password"])
        user.is_active = True
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, strip=False)
    generic_error = "The credentials are not valid."

    def clean(self):
        cleaned = super().clean()
        email = User.objects.normalize_email((cleaned.get("email") or "").strip())
        password = cleaned.get("password") or ""
        user = None
        if email and password:
            candidate = User.objects.filter(email__iexact=email, is_active=True).first()
            if candidate is not None and candidate.check_password(password):
                user = candidate
        if user is None:
            raise forms.ValidationError(self.generic_error)
        cleaned["user"] = user
        return cleaned
