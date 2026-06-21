from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("jobs/", views.job_list, name="jobs"),
    path("jobs/<slug:slug>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.apply_job, name="apply_job"),
    path("jobs/<int:job_id>/save/", views.save_job, name="save_job"),
    path("city-pools/", views.city_pools, name="city_pools"),
    path(
        "technicians/<int:technician_id>/",
        views.technician_profile_detail,
        name="technician_profile_detail",
    ),
    path(
        "employers/<int:employer_id>/",
        views.employer_profile_detail,
        name="employer_profile_detail",
    ),
    path("vault/", views.technician_vault, name="technician_vault"),
    path("documents/<int:document_id>/", views.serve_document, name="serve_document"),
    path(
        "certifications/<int:certification_id>/",
        views.serve_certification,
        name="serve_certification",
    ),
    path("employer/", views.employer_dashboard, name="employer_dashboard"),
    path("employer/jobs/new/", views.employer_job_create, name="employer_job_create"),
    path(
        "employer/jobs/<int:job_id>/edit/",
        views.employer_job_edit,
        name="employer_job_edit",
    ),
    path(
        "employer/jobs/<int:job_id>/status/",
        views.employer_job_status,
        name="employer_job_status",
    ),
    path(
        "employer/jobs/<int:job_id>/delete/",
        views.employer_job_delete,
        name="employer_job_delete",
    ),
    path(
        "employer/candidates/<int:technician_id>/invite/",
        views.invite_candidate,
        name="invite_candidate",
    ),
    path(
        "employer/candidates/<int:technician_id>/credentials/",
        views.request_credentials,
        name="request_credentials",
    ),
    path(
        "applications/<int:application_id>/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "applications/<int:application_id>/message/",
        views.application_message,
        name="application_message",
    ),
    path(
        "applications/<int:application_id>/stage/",
        views.update_application_stage,
        name="update_application_stage",
    ),
    path(
        "applications/<int:application_id>/respond/",
        views.respond_application,
        name="respond_application",
    ),
    path(
        "applications/<int:application_id>/withdraw/",
        views.withdraw_application,
        name="withdraw_application",
    ),
    path(
        "reviews/technicians/<int:technician_id>/",
        views.review_technician,
        name="review_technician",
    ),
    path(
        "reviews/employers/<int:employer_id>/",
        views.review_employer,
        name="review_employer",
    ),
    path("notifications/", views.notification_center, name="notification_center"),
    path(
        "notifications/read/",
        views.mark_notifications_read,
        name="mark_notifications_read",
    ),
    path("pricing/", views.pricing, name="pricing"),
    path("legal/", views.legal, name="legal"),
]
