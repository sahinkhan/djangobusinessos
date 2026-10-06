import re
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_login_uses_businessos_erp_design_and_existing_authentication(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b'class="erp-login-screen"' in response.content
    assert b"Enterprise Management &amp; ERP Cloud" in response.content
    assert b'name="username"' in response.content
    assert b'name="password"' in response.content
    assert b"csrfmiddlewaretoken" in response.content
    assert b"Quick Demo Logins" not in response.content
    assert b"Manage Databases" not in response.content

    invalid = client.post(
        reverse("login"),
        {"username": "missing@example.com", "password": "incorrect"},
    )

    assert invalid.status_code == 200
    assert b'class="erp-login-error"' in invalid.content


@pytest.mark.django_db
def test_login_page_remains_visible_when_opened_by_signed_in_user(client):
    user = get_user_model().objects.create_user("operator@example.com", "password")
    client.force_login(user)

    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b'class="erp-login-screen"' in response.content
    assert b'class="bos-shell ' not in response.content


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
    assert b"BusinessOS Dashboard" in response.content
    assert b"BUSINESS APPLICATIONS" in response.content
    assert b"Phase 1 contracts" not in response.content
    assert b"BusinessOS" in response.content
    assert b"css/tailwind.css" in response.content
    assert b"tailwindcss@2.2.19" not in response.content
    assert b'id="app-content"' in response.content
    assert b'id="bos-current-app"' in response.content
    assert b'id="bos-module-menu"' in response.content
    assert b'id="bos-company-context"' in response.content
    assert b'class="bos-app-grid"' in response.content
    assert b"odoo-" not in response.content
    assert b'aria-label="Search apps"' in response.content
    assert b"js/app-navigation.js" in response.content
    assert b"css/businessos.css?v=ui-recovery-1" in response.content
    assert b"js/app-navigation.js?v=ui-recovery-1" in response.content
    assert b'hx-history="false"' in response.content
    assert b'"historyCacheSize":0,"refreshOnHistoryMiss":true' in response.content
    assert b"$el.showModal()" in response.content
    assert b"@cancel.prevent=" in response.content
    assert b"closeLauncher()" in response.content
    assert b"openLauncher($event.currentTarget)" in response.content
    assert b"lg:pl-[17rem]" not in response.content
    assert b"data-app-nav" in response.content
    assert f'<form method="post" action="{reverse("logout")}"'.encode() in response.content


@pytest.mark.django_db
def test_htmx_get_keeps_full_page_progressive_response(client):
    user = get_user_model().objects.create_user("operator@example.com", "password")
    client.force_login(user)

    response = client.get(reverse("home"), HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert b"<!doctype html>" in response.content
    assert b'id="app-content"' in response.content
    assert b'class="app-sidebar ' in response.content
    assert b'id="bos-current-app"' in response.content


def test_shell_namespace_matches_templates_styles_and_navigation():
    project_root = Path(__file__).resolve().parents[1]
    styles = (project_root / "static/css/businessos.css").read_text(encoding="utf-8")
    navigation = (project_root / "static/js/app-navigation.js").read_text(encoding="utf-8")
    header = (project_root / "templates/components/header.html").read_text(encoding="utf-8")

    for identifier in ("bos-current-app", "bos-module-menu", "bos-company-context"):
        assert f'id="{identifier}"' in header
        assert f'"{identifier}"' in navigation
    assert ".bos-shell" in styles
    assert ".bos-app-grid" in styles
    styled_classes = set(re.findall(r"\.(bos-[a-z0-9-]+)", styles))
    header_ids = set(re.findall(r'id="(bos-[a-z0-9-]+)"', header))
    for path in (project_root / "templates").rglob("*.html"):
        attributes = re.findall(r'(?:class|id)="([^"]+)"', path.read_text(encoding="utf-8"))
        identifiers = set(re.findall(r"bos-[a-z0-9-]+", " ".join(attributes)))
        assert identifiers <= styled_classes | header_ids, path
    for directory, pattern in (("templates", "*.html"), ("static", "*.css"), ("static", "*.js")):
        for path in (project_root / directory).rglob(pattern):
            assert "odoo-" not in path.read_text(encoding="utf-8"), path


@pytest.mark.django_db
def test_login_also_installs_legacy_history_cache_protection(client):
    response = client.get(reverse("login"))
    assert b'hx-history="false"' in response.content
    assert b"js/app-navigation.js" in response.content
    assert b'id="app-content"' not in response.content
