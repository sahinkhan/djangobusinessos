from django.contrib.auth import views as auth_views
from django.urls import include, path

from businessos.core.admin import businessos_admin_site
from businessos.core.views import home, select_company

urlpatterns = [
    path("admin/", businessos_admin_site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("scope/company/", select_company, name="select_company"),
    path("parties/", include("businessos.modules.party.urls")),
    path("catalog/", include("businessos.modules.catalog.urls")),
    path("procurement/", include("businessos.modules.procurement.urls")),
    path("", home, name="home"),
]
