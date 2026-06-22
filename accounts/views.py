from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from billing.models import Invoice, Subscription
from marketplace.models import (
    Application,
    Certification,
    EmployerProfile,
    Job,
    TechnicianDocument,
    TechnicianProfile,
)

from .forms import EmployerRegistrationForm, LoginForm, TechnicianRegistrationForm
from .models import User


class WrenchLinkLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


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
        return redirect("accounts:operations")
    if request.user.role == User.Role.EMPLOYER:
        return redirect("employer_dashboard")
    return redirect("technician_vault")


@staff_required
def operations(request):
    search = request.GET.get("q", "").strip()[:100]
    users = User.objects.select_related(
        "technician_profile", "employer_profile", "subscription"
    ).order_by("-date_joined")
    if search:
        users = users.filter(
            Q(email__icontains=search)
            | Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    pending_documents = TechnicianDocument.objects.filter(
        status=TechnicianDocument.Status.PENDING
    ).select_related("technician__user")
    pending_certifications = Certification.objects.filter(
        status=Certification.Status.PENDING
    ).select_related("technician__user")
    subscriptions = Subscription.objects.select_related("user").order_by("-updated_at")
    invoices = Invoice.objects.select_related("subscription__user").order_by(
        "-created_at"
    )

    context = {
        "search": search,
        "users": users[:100],
        "user_count": User.objects.count(),
        "active_user_count": User.objects.filter(is_active=True).count(),
        "technician_count": TechnicianProfile.objects.count(),
        "employer_count": EmployerProfile.objects.count(),
        "pending_documents": pending_documents[:100],
        "pending_certifications": pending_certifications[:100],
        "reviewed_documents": TechnicianDocument.objects.exclude(
            status=TechnicianDocument.Status.PENDING
        )
        .select_related("technician__user")
        .order_by("-uploaded_at")[:50],
        "reviewed_certifications": Certification.objects.exclude(
            status=Certification.Status.PENDING
        )
        .select_related("technician__user")
        .order_by("-uploaded_at")[:50],
        "pending_review_count": pending_documents.count()
        + pending_certifications.count(),
        "technicians": TechnicianProfile.objects.select_related(
            "user", "city_pool"
        ).order_by("-updated_at")[:100],
        "employers": EmployerProfile.objects.select_related(
            "user", "city_pool"
        ).order_by("-updated_at")[:100],
        "jobs": Job.objects.select_related("employer", "city_pool")
        .annotate(application_total=Count("applications"))
        .order_by("-updated_at")[:100],
        "job_status_choices": Job.Status.choices,
        "application_count": Application.objects.count(),
        "subscriptions": subscriptions[:100],
        "active_subscription_count": subscriptions.filter(
            status=Subscription.Status.ACTIVE
        ).count(),
        "paid_invoice_total": invoices.filter(status="paid").aggregate(
            total=Sum("amount_due")
        )["total"]
        or 0,
        "invoices": invoices[:100],
    }
    return render(request, "accounts/operations.html", context)


@staff_required
@require_POST
def operations_user_action(request, user_id, action):
    user = get_object_or_404(User, pk=user_id)
    if user.is_staff:
        messages.error(request, "Staff accounts must be managed through secure Django administration.")
        return redirect(f"{reverse('accounts:operations')}#users")

    if action == "activate":
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "User account activated.")
    elif action == "suspend":
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, "User account suspended.")
    elif action == "verify-email":
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        messages.success(request, "User email marked as verified.")
    else:
        return HttpResponseBadRequest("Unsupported user action.")
    return redirect(f"{reverse('accounts:operations')}#users")


@staff_required
@require_POST
def operations_document_action(request, kind, object_id, decision):
    if kind == "document":
        item = get_object_or_404(TechnicianDocument, pk=object_id)
        if decision == "approve":
            item.status = TechnicianDocument.Status.VERIFIED
            item.is_verified = True
            item.rejection_reason = ""
        elif decision == "reject":
            item.status = TechnicianDocument.Status.REJECTED
            item.is_verified = False
            item.rejection_reason = request.POST.get("reason", "").strip()[:300]
        else:
            return HttpResponseBadRequest("Unsupported review decision.")
        item.save(update_fields=["status", "is_verified", "rejection_reason"])
    elif kind == "certification":
        item = get_object_or_404(Certification, pk=object_id)
        if decision == "approve":
            item.status = Certification.Status.VERIFIED
            item.is_verified = True
            item.rejection_reason = ""
        elif decision == "reject":
            item.status = Certification.Status.REJECTED
            item.is_verified = False
            item.rejection_reason = request.POST.get("reason", "").strip()[:300]
        else:
            return HttpResponseBadRequest("Unsupported review decision.")
        item.save(update_fields=["status", "is_verified", "rejection_reason"])
    else:
        return HttpResponseBadRequest("Unsupported document type.")

    messages.success(request, f"Review saved: {decision}.")
    return redirect(f"{reverse('accounts:operations')}#documents")


@staff_required
@require_POST
def operations_profile_action(request, kind, object_id, action):
    if kind == "employer":
        profile = get_object_or_404(EmployerProfile, pk=object_id)
        if action not in {"verify", "unverify"}:
            return HttpResponseBadRequest("Unsupported employer action.")
        profile.is_verified = action == "verify"
        profile.save(update_fields=["is_verified"])
    elif kind == "technician":
        profile = get_object_or_404(TechnicianProfile, pk=object_id)
        if action not in {"show", "hide"}:
            return HttpResponseBadRequest("Unsupported technician action.")
        profile.is_visible = action == "show"
        profile.save(update_fields=["is_visible"])
    else:
        return HttpResponseBadRequest("Unsupported profile type.")

    messages.success(request, "Profile moderation status updated.")
    return redirect(f"{reverse('accounts:operations')}#profiles")


@staff_required
@require_POST
def operations_job_status(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    status = request.POST.get("status", "")
    if status not in Job.Status.values:
        return HttpResponseBadRequest("Unsupported job status.")
    job.status = status
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Job status updated.")
    return redirect(f"{reverse('accounts:operations')}#marketplace")


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
