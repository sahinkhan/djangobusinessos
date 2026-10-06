"""Presentation recovery must coexist with the Gate UI-1 protections."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_recovered_dashboard_keeps_compact_shell_and_all_screen_launcher(client):
    user = get_user_model().objects.create_user("recovery@example.com", "password")
    client.force_login(user)
    response = client.get(reverse("home"))
    html = response.content.decode()
    assert "BusinessOS Dashboard" in html
    assert 'class="dashboard-home"' in html
    assert 'class="bos-app-grid"' in html
    assert 'id="bos-current-app"' in html
    assert 'id="bos-module-menu"' in html
    assert 'aria-label="Search applications"' in html
    assert 'hx-history="false"' in html
    assert '"historyCacheSize":0,"refreshOnHistoryMiss":true' in html
    dialog = html.split("<dialog", 1)[1].split("</dialog>", 1)[0]
    assert "$el.showModal()" in dialog
    assert "closeLauncher()" in dialog
    assert "lg:hidden" not in dialog
    assert "trapLauncherFocus" not in dialog
    assert "launcherOpener" in html
    assert "lg:pl-[17rem]" not in html
    assert "@resize.window" not in html


def test_recovered_styles_and_header_are_not_the_old_sidebar_design():
    root = Path(__file__).resolve().parents[1]
    styles = (root / "static/css/businessos.css").read_text(encoding="utf-8")
    header = (root / "templates/components/header.html").read_text(encoding="utf-8")
    assert "--bos-accent: #714b67" in styles
    assert "max-width: 1120px" in styles
    assert '"Plus Jakarta Sans"' in styles
    assert ".app-header { height: 44px;" in styles
    assert 'class="bos-nav-button"' in header
    assert 'class="bos-global-search"' in header
    assert header.count("openLauncher($event.currentTarget)") == 2


def test_login_card_controls_share_the_compact_responsive_container():
    root = Path(__file__).resolve().parents[1]
    styles = (root / "static/css/businessos.css").read_text(encoding="utf-8")
    card = styles.split(".erp-login-card {", 1)[1].split("}", 1)[0]
    input_control = styles.split(".erp-login-control input {", 1)[1].split("}", 1)[0]
    submit = styles.split(".erp-login-submit {", 1)[1].split("}", 1)[0]

    assert "width: 100%" in card
    assert "max-width: 24rem" in card
    assert "width: 100%" in input_control
    assert "width: 100%" in submit
    assert "max-width:" not in input_control
    assert "max-width:" not in submit


@pytest.mark.django_db
def test_recovered_login_has_no_authenticated_shell_or_snapshot_cache(client):
    response = client.get(reverse("login"))
    assert b'class="erp-login-screen"' in response.content
    assert b'class="bos-shell ' not in response.content
    assert b'hx-history="false"' in response.content
    assert b'"historyCacheSize":0' in response.content
    assert b"js/app-navigation.js?v=ui-recovery-1" in response.content
