from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from marketplace import views


urlpatterns = [
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("index.html", RedirectView.as_view(pattern_name="home", permanent=True)),
    path("home.html", RedirectView.as_view(pattern_name="home", permanent=True)),
    path("jobs.html", RedirectView.as_view(pattern_name="jobs", permanent=True)),
    path(
        "city-pools.html",
        RedirectView.as_view(pattern_name="city_pools", permanent=True),
    ),
    path(
        "vault.html",
        RedirectView.as_view(pattern_name="technician_vault", permanent=True),
    ),
    path(
        "employer.html",
        RedirectView.as_view(pattern_name="employer_dashboard", permanent=True),
    ),
    path(
        "billing.html",
        RedirectView.as_view(pattern_name="billing:overview", permanent=True),
    ),
    path("legal.html", RedirectView.as_view(pattern_name="legal", permanent=True)),
    path("pricing.html", RedirectView.as_view(url="/#pricing", permanent=True)),
    path("account/", include("accounts.urls")),
    path("", include("marketplace.urls")),
    path("billing/", include("billing.urls")),
]

handler404 = views.error_404
handler500 = views.error_500
