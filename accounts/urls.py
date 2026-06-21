from django.contrib.auth.views import LogoutView, PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView
from django.contrib.auth.views import PasswordResetView
from django.urls import path, reverse_lazy

from . import views


app_name = "accounts"

urlpatterns = [
    path("login/", views.WrenchLinkLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/technician/", views.register_technician, name="register_technician"),
    path("register/employer/", views.register_employer, name="register_employer"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("verify/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
