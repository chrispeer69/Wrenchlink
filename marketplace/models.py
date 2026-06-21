from django.conf import settings
from uuid import uuid4

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_private_document


def private_upload_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    owner_id = instance.technician_id or "unassigned"
    return f"private/technicians/{owner_id}/{uuid4().hex}.{extension}"


class CityPool(models.Model):
    class Region(models.TextChoices):
        MIDWEST = "Midwest", "Midwest"
        SOUTHEAST = "Southeast", "Southeast"
        NORTHEAST = "Northeast", "Northeast"
        SOUTHWEST = "Southwest", "Southwest"
        WEST = "West", "West"

    name = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    state_code = models.CharField(max_length=2)
    region = models.CharField(max_length=20, choices=Region.choices)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["region", "state", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "state_code"], name="unique_city_pool"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.state_code}")
        super().save(*args, **kwargs)

    @property
    def technician_count(self):
        return self.technicians.filter(is_visible=True).count()

    @property
    def open_job_count(self):
        return self.jobs.filter(status=Job.Status.ACTIVE).count()

    def __str__(self):
        return f"{self.name}, {self.state_code}"


class EmployerProfile(models.Model):
    class ShopType(models.TextChoices):
        REPAIR = "repair", "Auto Repair Shop"
        COLLISION = "collision", "Auto Body / Collision Shop"
        DEALER = "dealer", "Dealership Service Department"
        FLEET = "fleet", "Fleet Maintenance"
        GROUP = "group", "Multi-location Group"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    company_name = models.CharField(max_length=200)
    shop_type = models.CharField(max_length=20, choices=ShopType.choices)
    city_pool = models.ForeignKey(
        CityPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employers",
    )
    description = models.TextField(blank=True, max_length=2500)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    perks = models.JSONField(default=list, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class TechnicianProfile(models.Model):
    class Availability(models.TextChoices):
        ACTIVE = "active", "Actively Looking"
        PASSIVE = "passive", "Passively Open"
        CLOSED = "closed", "Not Looking"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technician_profile",
    )
    city_pool = models.ForeignKey(
        CityPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technicians",
    )
    professional_title = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, max_length=2000)
    phone = models.CharField(max_length=30, blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    availability = models.CharField(
        max_length=20, choices=Availability.choices, default=Availability.ACTIVE
    )
    preferred_schedule = models.CharField(max_length=100, blank=True)
    minimum_pay = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    willing_to_relocate = models.BooleanField(default=False)
    skills = models.JSONField(default=list, blank=True)
    is_visible = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    email_job_alerts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class Certification(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=150)
    issuing_organization = models.CharField(max_length=150, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    file = models.FileField(
        upload_to=private_upload_path,
        validators=[validate_private_document],
        null=True,
        blank=True,
    )
    content_type = models.CharField(max_length=150, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    is_verified = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.name


class WorkHistory(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="work_history"
    )
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, max_length=1500)

    class Meta:
        ordering = ["-start_date"]


class Education(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="education"
    )
    school = models.CharField(max_length=200)
    program = models.CharField(max_length=200)
    completion_year = models.PositiveSmallIntegerField(null=True, blank=True)


class ProfessionalReference(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="references"
    )
    name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)


class TechnicianDocument(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="documents"
    )
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to=private_upload_path,
        validators=[validate_private_document],
    )
    content_type = models.CharField(max_length=150, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Job(models.Model):
    class Category(models.TextChoices):
        REPAIR = "repair", "Auto Repair"
        BODY = "body", "Auto Body"
        PAINT = "paint", "Paint"
        ESTIMATOR = "estimator", "Estimator / Advisor"
        EV = "ev", "EV / Hybrid"
        DIESEL = "diesel", "Diesel / Fleet"

    class Schedule(models.TextChoices):
        FULL_TIME = "full_time", "Full-Time"
        PART_TIME = "part_time", "Part-Time"
        CONTRACT = "contract", "Contract"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        FILLED = "filled", "Filled"
        CLOSED = "closed", "Closed"

    employer = models.ForeignKey(
        EmployerProfile, on_delete=models.CASCADE, related_name="jobs"
    )
    city_pool = models.ForeignKey(
        CityPool, on_delete=models.SET_NULL, null=True, related_name="jobs"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    schedule = models.CharField(max_length=20, choices=Schedule.choices)
    pay_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pay_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    experience_years = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    certification_requirement = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=5000)
    benefits = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            root = slugify(f"{self.title}-{self.employer.company_name}")[:210]
            candidate = root
            number = 2
            while Job.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{root}-{number}"
                number += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("job_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.title} at {self.employer.company_name}"


class SavedJob(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="saved_jobs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "job"], name="unique_saved_job"
            )
        ]


class Application(models.Model):
    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        INVITED = "invited", "Invited"
        REVIEWED = "reviewed", "Reviewed"
        INTERVIEW = "interview", "Interview"
        OFFERED = "offered", "Offer Sent"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.APPLIED
    )
    employer_notes = models.TextField(blank=True, max_length=2000)
    invitation_message = models.CharField(max_length=600, blank=True)
    offer_details = models.CharField(max_length=1000, blank=True)
    interview_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "job"], name="unique_job_application"
            )
        ]


class ApplicationMessage(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class CredentialAccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    employer = models.ForeignKey(
        EmployerProfile, on_delete=models.CASCADE, related_name="credential_requests"
    )
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="credential_requests"
    )
    credential_type = models.CharField(max_length=150, default="all")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["employer", "technician", "credential_type"],
                name="unique_credential_access_request",
            )
        ]


class TechnicianReview(models.Model):
    employer = models.ForeignKey(
        EmployerProfile, on_delete=models.CASCADE, related_name="technician_reviews"
    )
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="reviews"
    )
    skill = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    reliability = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employer", "technician"],
                name="unique_employer_technician_review",
            )
        ]

    @property
    def average(self):
        return round((self.skill + self.reliability + self.communication) / 3, 1)


class EmployerReview(models.Model):
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="employer_reviews"
    )
    employer = models.ForeignKey(
        EmployerProfile, on_delete=models.CASCADE, related_name="reviews"
    )
    professionalism = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    workplace = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "employer"],
                name="unique_technician_employer_review",
            )
        ]

    @property
    def average(self):
        return round(
            (self.professionalism + self.communication + self.workplace) / 3, 1
        )


class Notification(models.Model):
    class Event(models.TextChoices):
        MESSAGE = "message", "Messages"
        APPLICATION = "application", "Application activity"
        OFFER = "offer", "Invitations and offers"
        CREDENTIAL = "credential", "Credential requests"
        JOB_MATCH = "job_match", "Matching jobs"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event = models.CharField(
        max_length=20, choices=Event.choices, default=Event.APPLICATION
    )
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=600)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    in_app_messages = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=True)
    in_app_applications = models.BooleanField(default=True)
    email_applications = models.BooleanField(default=True)
    in_app_offers = models.BooleanField(default=True)
    email_offers = models.BooleanField(default=True)
    in_app_credentials = models.BooleanField(default=True)
    email_credentials = models.BooleanField(default=True)
    in_app_job_matches = models.BooleanField(default=True)
    email_job_matches = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    EVENT_FIELDS = {
        Notification.Event.MESSAGE: ("in_app_messages", "email_messages"),
        Notification.Event.APPLICATION: (
            "in_app_applications",
            "email_applications",
        ),
        Notification.Event.OFFER: ("in_app_offers", "email_offers"),
        Notification.Event.CREDENTIAL: (
            "in_app_credentials",
            "email_credentials",
        ),
        Notification.Event.JOB_MATCH: (
            "in_app_job_matches",
            "email_job_matches",
        ),
    }

    def channels_for(self, event):
        in_app_field, email_field = self.EVENT_FIELDS[event]
        return getattr(self, in_app_field), getattr(self, email_field)
