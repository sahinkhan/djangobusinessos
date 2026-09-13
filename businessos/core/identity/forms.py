from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User
from .normalization import normalize_email_identity


class CanonicalEmailFormMixin:
    def clean_email(self):
        email = normalize_email_identity(self.cleaned_data["email"])
        matches = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email


class AdminUserCreationForm(CanonicalEmailFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)


class AdminUserChangeForm(CanonicalEmailFormMixin, UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
