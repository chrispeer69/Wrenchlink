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
    path("operations/", views.operations, name="operations"),
    path(
        "operations/users/<int:user_id>/message/",
        views.operations_send_message,
        name="operations_send_message",
    ),
    path(
        "operations/users/<int:user_id>/<str:action>/",
        views.operations_user_action,
        name="operations_user_action",
    ),
    path(
        "operations/documents/<str:kind>/<int:object_id>/<str:decision>/",
        views.operations_document_action,
        name="operations_document_action",
    ),
    path(
        "operations/profiles/<str:kind>/<int:object_id>/<str:action>/",
        views.operations_profile_action,
        name="operations_profile_action",
    ),
    path(
        "operations/jobs/<int:job_id>/status/",
        views.operations_job_status,
        name="operations_job_status",
    ),
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
