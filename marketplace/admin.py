from django.contrib import admin

from .models import Application, ApplicationMessage, Certification, CityPool
from .models import CredentialAccessRequest, Education, EmployerProfile, EmployerReview
from .models import Job, Notification, NotificationPreference, ProfessionalReference, SavedJob
from .models import TechnicianDocument, TechnicianProfile, TechnicianReview, WorkHistory


@admin.register(CityPool)
class CityPoolAdmin(admin.ModelAdmin):
    list_display = ("name", "state_code", "region", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("name", "state", "state_code")
    prepopulated_fields = {"slug": ("name", "state_code")}


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "shop_type", "city_pool", "is_verified")
    list_filter = ("shop_type", "is_verified", "city_pool")
    search_fields = ("company_name", "user__email")


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "professional_title",
        "city_pool",
        "availability",
        "is_visible",
    )
    list_filter = ("availability", "is_visible", "city_pool")
    search_fields = ("user__email", "user__first_name", "user__last_name")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "city_pool", "status", "created_at")
    list_filter = ("status", "category", "schedule", "city_pool")
    search_fields = ("title", "employer__company_name")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("technician", "job", "stage", "created_at")
    list_filter = ("stage",)
    search_fields = ("technician__user__email", "job__title")


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ("name", "technician", "status", "expiry_date", "uploaded_at")
    list_filter = ("status", "is_verified")
    search_fields = ("name", "technician__user__email", "credential_id")
    readonly_fields = ("uploaded_at", "content_type", "file_size")


@admin.register(TechnicianDocument)
class TechnicianDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "technician", "is_verified", "uploaded_at", "file_size")
    list_filter = ("is_verified", "uploaded_at")
    search_fields = ("name", "technician__user__email")
    readonly_fields = ("uploaded_at", "content_type", "file_size")


admin.site.register(
    [
        WorkHistory,
        Education,
        ProfessionalReference,
        SavedJob,
        ApplicationMessage,
        CredentialAccessRequest,
        TechnicianReview,
        EmployerReview,
        Notification,
        NotificationPreference,
    ]
)
admin.site.site_header = "WrenchLink Administration"
admin.site.site_title = "WrenchLink Admin"
admin.site.index_title = "Platform management"
