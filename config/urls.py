from django.contrib.auth import views as auth_views
from django.urls import path

from businessos.core.admin import businessos_admin_site
from businessos.core.views import home

urlpatterns = [
    path("admin/", businessos_admin_site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", home, name="home"),
]
