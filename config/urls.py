from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from marketplace import views


urlpatterns = [
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("account/", include("accounts.urls")),
    path("", include("marketplace.urls")),
    path("billing/", include("billing.urls")),
]

handler404 = views.error_404
handler500 = views.error_500
