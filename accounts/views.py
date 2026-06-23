from functools import wraps

from django.conf import settings
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
    Notification,
    TechnicianDocument,
    TechnicianProfile,
)

from .forms import EmployerRegistrationForm, LoginForm, TechnicianRegistrationForm
from .models import ModerationAction, User


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


def _moderation_notice(
    actor,
    target_user,
    action,
    subject,
    message,
    *,
    link="",
    object_type="",
    object_id=None,
):
    clean_subject = subject.strip()[:180]
    clean_message = message.strip()[:600]
    ModerationAction.objects.create(
        actor=actor,
        target_user=target_user,
        action=action[:60],
        subject=clean_subject,
        message=clean_message,
        object_type=object_type[:40],
        object_id=object_id,
    )
    Notification.objects.create(
        recipient=target_user,
        event=Notification.Event.SYSTEM,
        title=clean_subject[:150],
        body=clean_message,
        link=link[:300],
    )
    if target_user.email:
        send_mail(
            f"WrenchLink: {clean_subject[:120]}",
            f"{clean_message}\n\nSign in to WrenchLink to review this update.",
            settings.DEFAULT_FROM_EMAIL,
            [target_user.email],
            fail_silently=True,
        )


def _required_reason(request, label):
    reason = request.POST.get("reason", "").strip()[:600]
    if not reason:
        messages.error(request, f"Enter a reason before {label}.")
        return None
    return reason


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
        "moderation_actions": ModerationAction.objects.select_related(
            "actor", "target_user"
        )[:100],
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
        notice = request.POST.get("message", "").strip()[:600] or (
            "Your WrenchLink account has been reactivated. You can sign in and use the platform again."
        )
        _moderation_notice(
            request.user, user, "account_activated", "Account reactivated", notice
        )
        messages.success(request, "User account activated.")
    elif action == "suspend":
        reason = _required_reason(request, "suspending this account")
        if reason is None:
            return redirect(f"{reverse('accounts:operations')}#users")
        user.is_active = False
        user.save(update_fields=["is_active"])
        _moderation_notice(
            request.user,
            user,
            "account_suspended",
            "Account suspended",
            reason,
        )
        messages.success(request, "User account suspended.")
    elif action == "verify-email":
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        _moderation_notice(
            request.user,
            user,
            "email_verified",
            "Email verification completed",
            "WrenchLink staff verified the email address on your account.",
        )
        messages.success(request, "User email marked as verified.")
    else:
        return HttpResponseBadRequest("Unsupported user action.")
    return redirect(f"{reverse('accounts:operations')}#users")


@staff_required
@require_POST
def operations_document_action(request, kind, object_id, decision):
    if kind == "document":
        item = get_object_or_404(TechnicianDocument, pk=object_id)
        target_user = item.technician.user
        label = item.name
        link = reverse("technician_vault") + "#documents"
        if decision == "approve":
            item.status = TechnicianDocument.Status.VERIFIED
            item.is_verified = True
            item.rejection_reason = ""
            notice = (
                f'Your document "{label}" was approved and is now marked as verified.'
            )
        elif decision == "reject":
            reason = _required_reason(request, "rejecting this document")
            if reason is None:
                return redirect(f"{reverse('accounts:operations')}#documents")
            item.status = TechnicianDocument.Status.REJECTED
            item.is_verified = False
            item.rejection_reason = reason[:300]
            notice = f'Your document "{label}" was rejected. Reason: {reason}'
        else:
            return HttpResponseBadRequest("Unsupported review decision.")
        item.save(update_fields=["status", "is_verified", "rejection_reason"])
    elif kind == "certification":
        item = get_object_or_404(Certification, pk=object_id)
        target_user = item.technician.user
        label = item.name
        link = reverse("technician_vault") + "#certification"
        if decision == "approve":
            item.status = Certification.Status.VERIFIED
            item.is_verified = True
            item.rejection_reason = ""
            notice = (
                f'Your certification "{label}" was approved and is now verified.'
            )
        elif decision == "reject":
            reason = _required_reason(request, "rejecting this certification")
            if reason is None:
                return redirect(f"{reverse('accounts:operations')}#documents")
            item.status = Certification.Status.REJECTED
            item.is_verified = False
            item.rejection_reason = reason[:300]
            notice = f'Your certification "{label}" was rejected. Reason: {reason}'
        else:
            return HttpResponseBadRequest("Unsupported review decision.")
        item.save(update_fields=["status", "is_verified", "rejection_reason"])
    else:
        return HttpResponseBadRequest("Unsupported document type.")

    _moderation_notice(
        request.user,
        target_user,
        f"{kind}_{decision}",
        f"{label}: {decision.title()}",
        notice,
        link=link,
        object_type=kind,
        object_id=item.pk,
    )
    messages.success(request, f"Review saved and user notified: {decision}.")
    return redirect(f"{reverse('accounts:operations')}#documents")


@staff_required
@require_POST
def operations_profile_action(request, kind, object_id, action):
    if kind == "employer":
        profile = get_object_or_404(EmployerProfile, pk=object_id)
        if action not in {"verify", "reject", "unverify"}:
            return HttpResponseBadRequest("Unsupported employer action.")
        if action in {"reject", "unverify"}:
            notice = _required_reason(request, "removing employer verification")
            if notice is None:
                return redirect(f"{reverse('accounts:operations')}#profiles")
            profile.verification_status = EmployerProfile.VerificationStatus.REJECTED
            profile.rejection_reason = notice
        else:
            notice = (
                f"{profile.company_name} has been verified for use on WrenchLink."
            )
            profile.verification_status = EmployerProfile.VerificationStatus.VERIFIED
            profile.rejection_reason = ""
        profile.is_verified = action == "verify"
        profile.save(
            update_fields=["verification_status", "is_verified", "rejection_reason"]
        )
        target_user = profile.user
        subject = (
            "Employer profile verified"
            if action == "verify"
            else "Employer verification declined"
        )
    elif kind == "technician":
        profile = get_object_or_404(TechnicianProfile, pk=object_id)
        if action not in {"show", "hide"}:
            return HttpResponseBadRequest("Unsupported technician action.")
        if action == "hide":
            notice = _required_reason(request, "hiding this profile")
            if notice is None:
                return redirect(f"{reverse('accounts:operations')}#profiles")
        else:
            notice = "Your technician profile has been restored to marketplace search."
        profile.is_visible = action == "show"
        profile.save(update_fields=["is_visible"])
        target_user = profile.user
        subject = (
            "Technician profile restored"
            if action == "show"
            else "Technician profile hidden"
        )
    else:
        return HttpResponseBadRequest("Unsupported profile type.")

    _moderation_notice(
        request.user,
        target_user,
        f"{kind}_{action}",
        subject,
        notice,
        link=reverse("accounts:dashboard"),
        object_type=f"{kind}_profile",
        object_id=profile.pk,
    )
    messages.success(request, "Profile moderation status updated and user notified.")
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
    status_label = dict(Job.Status.choices)[status]
    notice = request.POST.get("message", "").strip()[:600] or (
        f'WrenchLink staff changed the status of "{job.title}" to {status_label}.'
    )
    _moderation_notice(
        request.user,
        job.employer.user,
        "job_status_changed",
        "Job status updated",
        notice,
        link=job.get_absolute_url(),
        object_type="job",
        object_id=job.pk,
    )
    messages.success(request, "Job status updated and employer notified.")
    return redirect(f"{reverse('accounts:operations')}#marketplace")


@staff_required
@require_POST
def operations_send_message(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    subject = request.POST.get("subject", "").strip()[:180]
    message_text = request.POST.get("message", "").strip()[:600]
    if not subject or not message_text:
        messages.error(request, "A subject and message are required.")
        return redirect(f"{reverse('accounts:operations')}#users")
    _moderation_notice(
        request.user,
        user,
        "staff_message",
        subject,
        message_text,
        link=reverse("accounts:dashboard"),
    )
    messages.success(request, "Message sent in WrenchLink and by email when available.")
    return redirect(f"{reverse('accounts:operations')}#users")


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
