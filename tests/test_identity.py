import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction

from businessos.core.identity.forms import AdminUserCreationForm


@pytest.mark.django_db
def test_user_creation_normalizes_email_and_hashes_password():
    user = get_user_model().objects.create_user("Owner@EXAMPLE.COM", "a-secure-password")

    assert user.email == "owner@example.com"
    assert user.check_password("a-secure-password")
    assert user.is_active
    assert not user.is_staff
    assert authenticate(email="OWNER@Example.com", password="a-secure-password") == user


@pytest.mark.django_db
def test_email_identity_is_case_insensitively_unique_in_forms_and_database():
    user_model = get_user_model()
    user_model.objects.create_user("owner@example.com", "a-secure-password")

    form = AdminUserCreationForm(
        data={
            "email": "Owner@EXAMPLE.COM",
            "password1": "another-secure-password",
            "password2": "another-secure-password",
        }
    )

    assert not form.is_valid()
    assert "email" in form.errors
    with pytest.raises(IntegrityError), transaction.atomic():
        user_model.objects.bulk_create([user_model(email="Owner@EXAMPLE.COM")])


@pytest.mark.django_db
def test_superuser_has_required_status_flags():
    user = get_user_model().objects.create_superuser("admin@example.com", "a-secure-password")

    assert user.is_staff
    assert user.is_superuser
    assert user.is_active
