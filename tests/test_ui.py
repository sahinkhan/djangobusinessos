import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_home_requires_authentication(client):
    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_authenticated_user_sees_application_shell(client):
    user = get_user_model().objects.create_user("operator@example.com", "password")
    client.force_login(user)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert b"Foundation ready" in response.content
    assert b"BusinessOS" in response.content
    assert b"css/tailwind.css" in response.content
    assert b"tailwindcss@2.2.19" not in response.content
