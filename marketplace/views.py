from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q, Sum
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import (
    ApplicationMessageForm,
    CertificationForm,
    EducationForm,
    EmployerProfileForm,
    EmployerReviewForm,
    JobForm,
    NotificationPreferenceForm,
    ProfessionalReferenceForm,
    TechnicianDocumentForm,
    TechnicianProfileForm,
    TechnicianReviewForm,
    WorkHistoryForm,
)
from .models import (
    Application,
    Certification,
    CityPool,
    CredentialAccessRequest,
    Education,
    EmployerProfile,
    EmployerReview,
    Job,
    Notification,
    NotificationPreference,
    ProfessionalReference,
    SavedJob,
    TechnicianDocument,
    TechnicianProfile,
    TechnicianReview,
    WorkHistory,
)
from .validators import MAX_TECHNICIAN_STORAGE, MAX_UPLOADS_PER_HOUR


def _is_technician(user):
    return user.is_authenticated and user.role == User.Role.TECHNICIAN


def _is_employer(user):
    return user.is_authenticated and user.role == User.Role.EMPLOYER


def _notify(user, event, title, body, link=""):
    preferences, _ = NotificationPreference.objects.get_or_create(user=user)
    in_app_enabled, email_enabled = preferences.channels_for(event)
    if in_app_enabled:
        Notification.objects.create(
            recipient=user,
            event=event,
            title=title[:150],
            body=body[:600],
            link=link[:300],
        )
    if user.email and email_enabled:
        send_mail(
            f"WrenchLink: {title[:120]}",
            f"{body[:600]}\n\nSign in to WrenchLink to review this update.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )


def _notify_job_match(job):
    technicians = TechnicianProfile.objects.filter(
        is_visible=True,
        city_pool=job.city_pool,
    ).select_related("user")
    for technician in technicians:
        _notify(
            technician.user,
            Notification.Event.JOB_MATCH,
            "New matching job",
            f"{job.employer.company_name} posted {job.title} in {job.city_pool}.",
            job.get_absolute_url(),
        )


def _upload_allowed(profile, upload):
    since = timezone.now() - timedelta(hours=1)
    recent_count = profile.documents.filter(uploaded_at__gte=since).count()
    recent_count += profile.certifications.filter(uploaded_at__gte=since).count()
    if recent_count >= MAX_UPLOADS_PER_HOUR:
        return False, "Upload limit reached. Try again in one hour."
    document_total = profile.documents.aggregate(total=Sum("file_size"))["total"] or 0
    credential_total = (
        profile.certifications.aggregate(total=Sum("file_size"))["total"] or 0
    )
    if document_total + credential_total + upload.size > MAX_TECHNICIAN_STORAGE:
        return False, "Your private vault is limited to 100 MB."
    return True, ""


def _safe_file_response(field_file, display_name):
    if not field_file:
        raise Http404
    try:
        handle = field_file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("File is unavailable.") from None
    extension = Path(field_file.name).suffix.lower()
    filename = get_valid_filename(f"{display_name}{extension}")
    response = FileResponse(handle, as_attachment=True, filename=filename)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


def home(request):
    jobs = (
        Job.objects.filter(status=Job.Status.ACTIVE)
        .select_related("employer", "city_pool")[:3]
    )
    return render(request, "marketplace/home.html", {"jobs": jobs})


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def job_list(request):
    jobs = Job.objects.filter(status=Job.Status.ACTIVE).select_related(
        "employer", "city_pool"
    )
    query = request.GET.get("q", "").strip()[:100]
    metro = request.GET.get("metro", "").strip()
    category = request.GET.get("category", "").strip()
    schedule = request.GET.get("schedule", "").strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(employer__company_name__icontains=query)
        )
    if metro:
        jobs = jobs.filter(city_pool__slug=metro)
    if category:
        jobs = jobs.filter(category=category)
    if schedule:
        jobs = jobs.filter(schedule=schedule)
    sort = request.GET.get("sort", "newest")
    if sort == "pay_desc":
        jobs = jobs.order_by("-pay_max", "-pay_min", "-created_at")
    elif sort == "pay_asc":
        jobs = jobs.order_by("pay_min", "created_at")
    elif sort == "experience":
        jobs = jobs.order_by("experience_years", "-created_at")
    applied_ids = set()
    saved_ids = set()
    if _is_technician(request.user):
        profile = request.user.technician_profile
        applied_ids = set(profile.applications.values_list("job_id", flat=True))
        saved_ids = set(profile.saved_jobs.values_list("job_id", flat=True))
    return render(
        request,
        "marketplace/jobs.html",
        {
            "jobs": jobs,
            "pools": CityPool.objects.filter(is_active=True),
            "categories": Job.Category.choices,
            "schedules": Job.Schedule.choices,
            "applied_ids": applied_ids,
            "saved_ids": saved_ids,
            "selected_sort": sort,
        },
    )


def job_detail(request, slug):
    job = get_object_or_404(
        Job.objects.select_related("employer", "city_pool"),
        slug=slug,
        status=Job.Status.ACTIVE,
    )
    application = None
    is_saved = False
    if _is_technician(request.user):
        profile = request.user.technician_profile
        application = Application.objects.filter(technician=profile, job=job).first()
        is_saved = SavedJob.objects.filter(technician=profile, job=job).exists()
    return render(
        request,
        "marketplace/job_detail.html",
        {"job": job, "application": application, "is_saved": is_saved},
    )


def city_pools(request):
    pools = CityPool.objects.filter(is_active=True)
    region = request.GET.get("region", "")
    if region:
        pools = pools.filter(region=region)
    return render(
        request,
        "marketplace/city_pools.html",
        {"pools": pools, "regions": CityPool.Region.choices, "selected_region": region},
    )


@login_required
def technician_profile_detail(request, technician_id):
    technician = get_object_or_404(
        TechnicianProfile.objects.select_related("user", "city_pool").prefetch_related(
            "certifications", "work_history", "education", "reviews"
        ),
        pk=technician_id,
        is_visible=True,
    )
    is_owner = _is_technician(request.user) and technician.user_id == request.user.id
    if not (is_owner or _is_employer(request.user) or request.user.is_staff):
        return HttpResponseForbidden("Employer access required.")
    employer = request.user.employer_profile if _is_employer(request.user) else None
    can_view_credentials = bool(
        employer and _may_view_private_files(request.user, technician)
    )
    active_jobs = employer.jobs.filter(status=Job.Status.ACTIVE) if employer else []
    return render(
        request,
        "marketplace/technician_profile.html",
        {
            "profile": technician,
            "is_owner": is_owner,
            "employer": employer,
            "can_view_credentials": can_view_credentials,
            "active_jobs": active_jobs,
        },
    )


def employer_profile_detail(request, employer_id):
    employer = get_object_or_404(
        EmployerProfile.objects.select_related("city_pool").prefetch_related("reviews"),
        pk=employer_id,
    )
    return render(
        request,
        "marketplace/employer_profile.html",
        {
            "employer": employer,
            "jobs": employer.jobs.filter(status=Job.Status.ACTIVE),
        },
    )


def _vault_forms(request, profile, action):
    post = request.POST if request.method == "POST" else None
    files = request.FILES if request.method == "POST" else None
    return {
        "profile_form": TechnicianProfileForm(
            post if action == "profile" else None, instance=profile
        ),
        "document_form": TechnicianDocumentForm(
            post if action == "document" else None,
            files if action == "document" else None,
        ),
        "certification_form": CertificationForm(
            post if action == "certification" else None,
            files if action == "certification" else None,
        ),
        "work_form": WorkHistoryForm(post if action == "work" else None),
        "education_form": EducationForm(post if action == "education" else None),
        "reference_form": ProfessionalReferenceForm(
            post if action == "reference" else None
        ),
    }


@login_required
def technician_vault(request):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    profile = request.user.technician_profile
    action = request.POST.get("action", "") if request.method == "POST" else ""
    forms = _vault_forms(request, profile, action)
    preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
    preference_form = NotificationPreferenceForm(
        request.POST if action == "notifications" else None,
        instance=preferences,
    )

    if request.method == "POST":
        if action == "notifications" and preference_form.is_valid():
            preference_form.save()
            messages.success(request, "Notification preferences updated.")
            return redirect("/vault/#notifications")
        model_actions = {
            "profile": (forms["profile_form"], None),
            "document": (forms["document_form"], TechnicianDocument),
            "certification": (forms["certification_form"], Certification),
            "work": (forms["work_form"], WorkHistory),
            "education": (forms["education_form"], Education),
            "reference": (forms["reference_form"], ProfessionalReference),
        }
        if action in model_actions:
            form, model = model_actions[action]
            if form.is_valid():
                record = form.save(commit=False)
                if model:
                    record.technician = profile
                upload = getattr(record, "file", None)
                if upload:
                    allowed, reason = _upload_allowed(profile, upload)
                    if not allowed:
                        form.add_error("file", reason)
                    else:
                        record.save()
                        messages.success(request, "Your vault has been updated.")
                        return redirect(f"{redirect('technician_vault').url}#{action}")
                else:
                    record.save()
                    messages.success(request, "Your vault has been updated.")
                    return redirect(f"{redirect('technician_vault').url}#{action}")

        delete_models = {
            "delete_document": TechnicianDocument,
            "delete_certification": Certification,
            "delete_work": WorkHistory,
            "delete_education": Education,
            "delete_reference": ProfessionalReference,
        }
        if action in delete_models:
            record = get_object_or_404(
                delete_models[action],
                pk=request.POST.get("record_id"),
                technician=profile,
            )
            file_field = getattr(record, "file", None)
            with transaction.atomic():
                record.delete()
                if file_field:
                    file_field.delete(save=False)
            messages.success(request, "Entry removed.")
            return redirect("technician_vault")

        if action == "credential_response":
            access = get_object_or_404(
                CredentialAccessRequest,
                pk=request.POST.get("request_id"),
                technician=profile,
            )
            decision = request.POST.get("decision")
            if decision not in {
                CredentialAccessRequest.Status.APPROVED,
                CredentialAccessRequest.Status.REJECTED,
            }:
                return HttpResponseForbidden("Invalid response.")
            access.status = decision
            access.responded_at = timezone.now()
            access.save(update_fields=["status", "responded_at"])
            _notify(
                access.employer.user,
                Notification.Event.CREDENTIAL,
                "Credential request updated",
                f"{profile} {decision} your credential access request.",
                "/employer/#applicants",
            )
            messages.success(request, f"Request {decision}.")
            return redirect("technician_vault")

    context = {
        "profile": profile,
        **forms,
        "applications": profile.applications.select_related(
            "job", "job__employer"
        ).prefetch_related("messages"),
        "saved_jobs": profile.saved_jobs.select_related("job", "job__employer"),
        "access_requests": profile.credential_requests.select_related("employer"),
        "preference_form": preference_form,
        "dashboard_notifications": request.user.notifications.all()[:8],
    }
    return render(request, "marketplace/technician_vault.html", context)


@login_required
def employer_dashboard(request):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    employer = request.user.employer_profile
    action = request.POST.get("action", "") if request.method == "POST" else ""
    form = EmployerProfileForm(
        request.POST
        if request.method == "POST" and action in {"", "profile"}
        else None,
        instance=employer,
    )
    preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
    preference_form = NotificationPreferenceForm(
        request.POST if action == "notifications" else None,
        instance=preferences,
    )
    if request.method == "POST" and action == "notifications" and preference_form.is_valid():
        preference_form.save()
        messages.success(request, "Notification preferences updated.")
        return redirect("/employer/#notifications")
    if request.method == "POST" and action in {"", "profile"} and form.is_valid():
        form.save()
        messages.success(request, "Business profile updated.")
        return redirect("employer_dashboard")

    jobs = employer.jobs.prefetch_related("applications")
    applications = Application.objects.filter(job__employer=employer).select_related(
        "technician__user", "technician__city_pool", "job"
    )
    candidates = TechnicianProfile.objects.filter(is_visible=True).select_related(
        "user", "city_pool"
    )
    query = request.GET.get("candidate_q", "").strip()[:100]
    city = request.GET.get("candidate_city", "").strip()
    availability = request.GET.get("availability", "").strip()
    if query:
        candidates = candidates.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(professional_title__icontains=query)
            | Q(bio__icontains=query)
        )
    if city:
        candidates = candidates.filter(city_pool__slug=city)
    elif employer.city_pool and not query:
        candidates = candidates.filter(city_pool=employer.city_pool)
    if availability:
        candidates = candidates.filter(availability=availability)

    return render(
        request,
        "marketplace/employer_dashboard.html",
        {
            "employer": employer,
            "form": form,
            "jobs": jobs,
            "candidates": candidates[:50],
            "applications": applications,
            "pools": CityPool.objects.filter(is_active=True),
            "availability_choices": TechnicianProfile.Availability.choices,
            "access_requests": employer.credential_requests.select_related(
                "technician__user"
            ),
            "preference_form": preference_form,
            "dashboard_notifications": request.user.notifications.all()[:8],
        },
    )


@login_required
def employer_job_create(request):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user.employer_profile
        job.save()
        if job.status == Job.Status.ACTIVE:
            _notify_job_match(job)
        messages.success(request, "Job saved.")
        return redirect("employer_dashboard")
    return render(
        request,
        "marketplace/job_form.html",
        {"form": form, "heading": "Create a job post", "submit_label": "Save job"},
    )


@login_required
def employer_job_edit(request, job_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    job = get_object_or_404(
        Job, pk=job_id, employer=request.user.employer_profile
    )
    was_active = job.status == Job.Status.ACTIVE
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        job = form.save()
        if job.status == Job.Status.ACTIVE and not was_active:
            _notify_job_match(job)
        messages.success(request, "Job updated.")
        return redirect("employer_dashboard")
    return render(
        request,
        "marketplace/job_form.html",
        {"form": form, "job": job, "heading": "Edit job post", "submit_label": "Update job"},
    )


@login_required
@require_POST
def employer_job_status(request, job_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    job = get_object_or_404(
        Job, pk=job_id, employer=request.user.employer_profile
    )
    status = request.POST.get("status")
    if status not in Job.Status.values:
        return HttpResponseForbidden("Invalid status.")
    was_active = job.status == Job.Status.ACTIVE
    job.status = status
    job.save(update_fields=["status", "updated_at"])
    if status == Job.Status.ACTIVE and not was_active:
        _notify_job_match(job)
    messages.success(request, f"Job marked {job.get_status_display().lower()}.")
    return redirect("employer_dashboard")


@login_required
@require_POST
def employer_job_delete(request, job_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    job = get_object_or_404(
        Job, pk=job_id, employer=request.user.employer_profile
    )
    title = job.title
    job.delete()
    messages.success(request, f'"{title}" was deleted.')
    return redirect("employer_dashboard")


@login_required
@require_POST
def invite_candidate(request, technician_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    employer = request.user.employer_profile
    technician = get_object_or_404(
        TechnicianProfile, pk=technician_id, is_visible=True
    )
    job = get_object_or_404(
        Job,
        pk=request.POST.get("job_id"),
        employer=employer,
        status=Job.Status.ACTIVE,
    )
    application, created = Application.objects.get_or_create(
        technician=technician,
        job=job,
        defaults={
            "stage": Application.Stage.INVITED,
            "invitation_message": request.POST.get("message", "").strip()[:600],
        },
    )
    if not created and application.stage in {
        Application.Stage.REJECTED,
        Application.Stage.WITHDRAWN,
    }:
        application.stage = Application.Stage.INVITED
        application.save(update_fields=["stage", "updated_at"])
    _notify(
        technician.user,
        Notification.Event.OFFER,
        "New job invitation",
        f"{employer.company_name} invited you to discuss {job.title}.",
        "/vault/#applications",
    )
    messages.success(request, f"Invitation sent to {technician}.")
    return redirect("employer_dashboard")


@login_required
@require_POST
def request_credentials(request, technician_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    technician = get_object_or_404(TechnicianProfile, pk=technician_id)
    credential_type = request.POST.get("credential_type", "all").strip()[:150] or "all"
    access, created = CredentialAccessRequest.objects.get_or_create(
        employer=request.user.employer_profile,
        technician=technician,
        credential_type=credential_type,
    )
    if not created and access.status == CredentialAccessRequest.Status.REJECTED:
        access.status = CredentialAccessRequest.Status.PENDING
        access.responded_at = None
        access.save(update_fields=["status", "responded_at"])
    _notify(
        technician.user,
        Notification.Event.CREDENTIAL,
        "Credential access requested",
        f"{request.user.employer_profile.company_name} requested access to {credential_type}.",
        "/vault/#credentials",
    )
    messages.success(request, "Credential request sent.")
    return redirect("employer_dashboard")


@login_required
def application_detail(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related(
            "job__employer__user", "technician__user", "technician__city_pool"
        ).prefetch_related("messages__sender"),
        pk=application_id,
    )
    is_owner = _is_technician(request.user) and application.technician.user_id == request.user.id
    is_hiring = _is_employer(request.user) and application.job.employer.user_id == request.user.id
    if not (is_owner or is_hiring or request.user.is_staff):
        return HttpResponseForbidden("You are not part of this application.")
    can_view_credentials = is_hiring and _may_view_private_files(
        request.user, application.technician
    )
    approved_certifications = (
        application.technician.certifications.filter(
            status=Certification.Status.VERIFIED
        )
        if can_view_credentials
        else []
    )
    approved_documents = (
        application.technician.documents.filter(is_verified=True)
        if can_view_credentials
        else []
    )
    return render(
        request,
        "marketplace/application_detail.html",
        {
            "application": application,
            "message_form": ApplicationMessageForm(),
            "is_owner": is_owner,
            "is_hiring": is_hiring,
            "stage_choices": Application.Stage.choices,
            "can_view_credentials": can_view_credentials,
            "approved_certifications": approved_certifications,
            "approved_documents": approved_documents,
            "technician_review_form": TechnicianReviewForm(),
            "employer_review_form": EmployerReviewForm(),
        },
    )


@login_required
@require_POST
def application_message(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related("job__employer__user", "technician__user"),
        pk=application_id,
    )
    participant_ids = {
        application.technician.user_id,
        application.job.employer.user_id,
    }
    if request.user.id not in participant_ids:
        return HttpResponseForbidden("You are not part of this application.")
    form = ApplicationMessageForm(request.POST)
    recent = list(application.messages.order_by("-created_at")[:2])
    if len(recent) == 2 and all(item.sender_id == request.user.id for item in recent):
        messages.error(request, "Wait for a reply before sending another message.")
    elif form.is_valid():
        item = form.save(commit=False)
        item.application = application
        item.sender = request.user
        item.save()
        recipient_id = next(user_id for user_id in participant_ids if user_id != request.user.id)
        recipient = User.objects.get(pk=recipient_id)
        _notify(
            recipient,
            Notification.Event.MESSAGE,
            "New application message",
            f"You have a new message about {application.job.title}.",
            f"/applications/{application.id}/",
        )
        messages.success(request, "Message sent.")
    else:
        messages.error(request, "Message must be 600 characters or fewer.")
    return redirect("application_detail", application_id=application.id)


@login_required
@require_POST
def update_application_stage(request, application_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    application = get_object_or_404(
        Application,
        pk=application_id,
        job__employer=request.user.employer_profile,
    )
    stage = request.POST.get("stage")
    allowed = {
        Application.Stage.REVIEWED,
        Application.Stage.INTERVIEW,
        Application.Stage.OFFERED,
        Application.Stage.REJECTED,
    }
    if stage not in allowed:
        return HttpResponseForbidden("Invalid stage.")
    application.stage = stage
    application.offer_details = request.POST.get("offer_details", "").strip()[:1000]
    application.employer_notes = request.POST.get("employer_notes", "").strip()[:2000]
    interview_value = request.POST.get("interview_at", "").strip()
    if interview_value:
        interview_at = parse_datetime(interview_value)
        if interview_at is None:
            messages.error(request, "Enter a valid interview date and time.")
            return redirect("application_detail", application_id=application.id)
        if timezone.is_naive(interview_at):
            interview_at = timezone.make_aware(interview_at)
        application.interview_at = interview_at
    elif stage != Application.Stage.INTERVIEW:
        application.interview_at = None
    application.save(
        update_fields=[
            "stage",
            "offer_details",
            "employer_notes",
            "interview_at",
            "updated_at",
        ]
    )
    _notify(
        application.technician.user,
        (
            Notification.Event.OFFER
            if stage == Application.Stage.OFFERED
            else Notification.Event.APPLICATION
        ),
        "Application updated",
        f"Your application for {application.job.title} is now {application.get_stage_display()}.",
        f"/applications/{application.id}/",
    )
    messages.success(request, "Application stage updated.")
    return redirect("application_detail", application_id=application.id)


@login_required
@require_POST
def respond_application(request, application_id):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    application = get_object_or_404(
        Application, pk=application_id, technician=request.user.technician_profile
    )
    response = request.POST.get("response")
    if application.stage == Application.Stage.INVITED:
        application.stage = (
            Application.Stage.INTERVIEW
            if response == "accept"
            else Application.Stage.WITHDRAWN
        )
    elif application.stage == Application.Stage.OFFERED:
        application.stage = (
            Application.Stage.HIRED
            if response == "accept"
            else Application.Stage.WITHDRAWN
        )
    else:
        return HttpResponseForbidden("This application is not awaiting a response.")
    application.save(update_fields=["stage", "updated_at"])
    _notify(
        application.job.employer.user,
        Notification.Event.OFFER,
        "Candidate response",
        f"{application.technician} {response}ed your request for {application.job.title}.",
        f"/applications/{application.id}/",
    )
    messages.success(request, f"Response recorded: {response}.")
    return redirect("application_detail", application_id=application.id)


@login_required
@require_POST
def withdraw_application(request, application_id):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    application = get_object_or_404(
        Application, pk=application_id, technician=request.user.technician_profile
    )
    if application.stage == Application.Stage.HIRED:
        return HttpResponseForbidden("A completed hire cannot be withdrawn here.")
    application.stage = Application.Stage.WITHDRAWN
    application.save(update_fields=["stage", "updated_at"])
    messages.success(request, "Application withdrawn.")
    return redirect("technician_vault")


def _may_view_private_files(user, technician, credential_type="all"):
    if user.is_staff:
        return True
    if _is_technician(user) and technician.user_id == user.id:
        return True
    if _is_employer(user):
        return CredentialAccessRequest.objects.filter(
            employer=user.employer_profile,
            technician=technician,
            status=CredentialAccessRequest.Status.APPROVED,
        ).filter(
            Q(credential_type__iexact="all")
            | Q(credential_type__iexact=credential_type)
        ).exists()
    return False


@login_required
def serve_document(request, document_id):
    document = get_object_or_404(
        TechnicianDocument.objects.select_related("technician__user"), pk=document_id
    )
    is_owner = _is_technician(request.user) and document.technician.user_id == request.user.id
    if _is_employer(request.user) and not document.is_verified:
        return HttpResponseForbidden("This document is pending security review.")
    if not (is_owner or request.user.is_staff) and not _may_view_private_files(
        request.user, document.technician, "documents"
    ):
        return HttpResponseForbidden("Approved credential access is required.")
    return _safe_file_response(document.file, document.name)


@login_required
def serve_certification(request, certification_id):
    certification = get_object_or_404(
        Certification.objects.select_related("technician__user"), pk=certification_id
    )
    is_owner = (
        _is_technician(request.user)
        and certification.technician.user_id == request.user.id
    )
    if _is_employer(request.user) and certification.status != Certification.Status.VERIFIED:
        return HttpResponseForbidden("This credential is pending security review.")
    if not (is_owner or request.user.is_staff) and not _may_view_private_files(
        request.user, certification.technician, certification.name
    ):
        return HttpResponseForbidden("Approved credential access is required.")
    return _safe_file_response(certification.file, certification.name)


@login_required
@require_POST
def apply_job(request, job_id):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.ACTIVE)
    application, created = Application.objects.get_or_create(
        technician=request.user.technician_profile, job=job
    )
    if created:
        _notify(
            job.employer.user,
            Notification.Event.APPLICATION,
            "New application",
            f"{request.user.technician_profile} applied for {job.title}.",
            f"/applications/{application.id}/",
        )
    messages.success(
        request, "Application submitted." if created else "You already applied."
    )
    return redirect(request.POST.get("next") or "jobs")


@login_required
@require_POST
def save_job(request, job_id):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    job = get_object_or_404(Job, pk=job_id, status=Job.Status.ACTIVE)
    saved, created = SavedJob.objects.get_or_create(
        technician=request.user.technician_profile, job=job
    )
    if not created:
        saved.delete()
    messages.success(request, "Job saved." if created else "Job removed from saved jobs.")
    return redirect(request.POST.get("next") or "jobs")


@login_required
@require_POST
def review_technician(request, technician_id):
    if not _is_employer(request.user):
        return HttpResponseForbidden("Employer account required.")
    technician = get_object_or_404(TechnicianProfile, pk=technician_id)
    if not Application.objects.filter(
        technician=technician,
        job__employer=request.user.employer_profile,
        stage=Application.Stage.HIRED,
    ).exists():
        return HttpResponseForbidden("Only hired technicians can be reviewed.")
    form = TechnicianReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.employer = request.user.employer_profile
        review.technician = technician
        TechnicianReview.objects.update_or_create(
            employer=review.employer,
            technician=technician,
            defaults={
                "skill": review.skill,
                "reliability": review.reliability,
                "communication": review.communication,
                "comment": review.comment,
            },
        )
        messages.success(request, "Technician review saved.")
    return redirect("employer_dashboard")


@login_required
@require_POST
def review_employer(request, employer_id):
    if not _is_technician(request.user):
        return HttpResponseForbidden("Technician account required.")
    employer = get_object_or_404(EmployerProfile, pk=employer_id)
    if not Application.objects.filter(
        technician=request.user.technician_profile,
        job__employer=employer,
        stage=Application.Stage.HIRED,
    ).exists():
        return HttpResponseForbidden("Only employers who hired you can be reviewed.")
    form = EmployerReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.technician = request.user.technician_profile
        review.employer = employer
        EmployerReview.objects.update_or_create(
            technician=review.technician,
            employer=employer,
            defaults={
                "professionalism": review.professionalism,
                "communication": review.communication,
                "workplace": review.workplace,
                "comment": review.comment,
            },
        )
        messages.success(request, "Employer review saved.")
    return redirect("technician_vault")


@login_required
def notification_center(request):
    return render(
        request,
        "marketplace/notifications.html",
        {"notifications": request.user.notifications.all()[:100]},
    )


@login_required
@require_POST
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    next_url = request.POST.get("next", "")
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("notification_center")


def pricing(request):
    return redirect("/#pricing", permanent=True)


def legal(request):
    return render(request, "marketplace/legal.html")


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
