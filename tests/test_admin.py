import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse


@pytest.mark.django_db
def test_core_admin_rejects_non_superuser_staff_even_with_model_permissions(client, company):
    staff_user = get_user_model().objects.create_user(
        "staff@example.com", "password", is_staff=True
    )
    staff_user.user_permissions.add(
        Permission.objects.get(codename="view_company"),
        Permission.objects.get(codename="change_company"),
    )
    client.force_login(staff_user)
    change_url = reverse("businessos_admin:organization_company_change", args=[company.id])

    response = client.post(
        change_url,
        {
            "code": company.code,
            "name": "Unauthorized change",
            "base_currency": company.base_currency_id,
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    company.refresh_from_db()
    assert company.name != "Unauthorized change"


@pytest.mark.django_db
def test_core_admin_allows_deployment_superuser(client):
    superuser = get_user_model().objects.create_superuser("admin@example.com", "password")
    client.force_login(superuser)

    response = client.get(reverse("businessos_admin:index"))

    assert response.status_code == 200
