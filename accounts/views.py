from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import EmployerRegistrationForm, LoginForm, TechnicianRegistrationForm
from .models import User


class WrenchLinkLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def _send_verification(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = request.build_absolute_uri(
        reverse("accounts:verify_email", kwargs={"uidb64": uid, "token": token})
    )
    send_mail(
        "Verify your WrenchLink email",
        f"Verify your WrenchLink account:\n\n{url}\n\nIf you did not register, ignore this message.",
        None,
        [user.email],
    )


def register_technician(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = TechnicianRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        try:
            _send_verification(request, user)
            messages.success(request, "Check your email to verify your account.")
        except Exception:
            messages.warning(
                request,
                "Your account was created, but the verification email could not be sent. Contact support to verify it.",
            )
        return redirect("accounts:login")
    return render(request, "accounts/register_technician.html", {"form": form})


def register_employer(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = EmployerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        try:
            _send_verification(request, user)
            messages.success(request, "Check your email to verify your account.")
        except Exception:
            messages.warning(
                request,
                "Your account was created, but the verification email could not be sent. Contact support to verify it.",
            )
        return redirect("accounts:login")
    return render(request, "accounts/register_employer.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin:index")
    if request.user.role == User.Role.EMPLOYER:
        return redirect("employer_dashboard")
    return redirect("technician_vault")


def verify_email(request, uidb64, token):
    try:
        user_id = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return HttpResponseBadRequest("Invalid verification link.")
    if not default_token_generator.check_token(user, token):
        return HttpResponseBadRequest("This verification link is invalid or expired.")
    if not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
    messages.success(request, "Email verified. You can now sign in.")
    return redirect("accounts:login")
