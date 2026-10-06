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
    assert b"Welcome to BusinessOS" in response.content
    assert b"Available business areas" in response.content
    assert b"Phase 1 contracts" not in response.content
    assert b"BusinessOS" in response.content
    assert b"css/tailwind.css" in response.content
    assert b"tailwindcss@2.2.19" not in response.content
    assert b'id="app-content"' in response.content
    assert b"js/app-navigation.js" in response.content
    assert b"data-app-nav" in response.content
    assert f'<form method="post" action="{reverse("logout")}"'.encode() in response.content
    assert b'hx-history="false"' in response.content
    assert b'"historyCacheSize":0,"refreshOnHistoryMiss":true' in response.content
    assert b"$el.showModal()" in response.content
    assert b"@cancel.prevent=" in response.content


@pytest.mark.django_db
def test_login_also_installs_legacy_history_cache_protection(client):
    response = client.get(reverse("login"))
    assert b'hx-history="false"' in response.content
    assert b"js/app-navigation.js" in response.content
    assert b'id="app-content"' not in response.content


@pytest.mark.django_db
def test_htmx_get_keeps_full_page_progressive_response(client):
    user = get_user_model().objects.create_user("operator@example.com", "password")
    client.force_login(user)

    response = client.get(reverse("home"), HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert b"<!doctype html>" in response.content
    assert b'id="app-content"' in response.content
    assert b'class="app-sidebar ' in response.content
