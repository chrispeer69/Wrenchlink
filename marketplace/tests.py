import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.management import call_command

from accounts.models import User

from .models import (
    Application,
    ApplicationMessage,
    Certification,
    CityPool,
    CredentialAccessRequest,
    Education,
    EmployerProfile,
    Job,
    Notification,
    NotificationPreference,
    TechnicianDocument,
    TechnicianProfile,
    WorkHistory,
)
from .validators import MAX_DOCUMENT_SIZE


class MarketplaceTests(TestCase):
    def setUp(self):
        self.pool = CityPool.objects.create(
            name="Columbus",
            state="Ohio",
            state_code="OH",
            region=CityPool.Region.MIDWEST,
        )
        self.employer_user = User.objects.create_user(
            username="shop@example.com",
            email="shop@example.com",
            role=User.Role.EMPLOYER,
            email_verified=True,
            password="A-long-test-password-821!",
        )
        self.employer = EmployerProfile.objects.create(
            user=self.employer_user,
            company_name="Apex Auto",
            shop_type=EmployerProfile.ShopType.REPAIR,
            city_pool=self.pool,
        )
        self.job = Job.objects.create(
            employer=self.employer,
            city_pool=self.pool,
            title="Diagnostic Technician",
            category=Job.Category.REPAIR,
            schedule=Job.Schedule.FULL_TIME,
            description="Electrical and drivability diagnostics.",
            status=Job.Status.ACTIVE,
        )
        self.tech_user = User.objects.create_user(
            username="tech@example.com",
            email="tech@example.com",
            role=User.Role.TECHNICIAN,
            email_verified=True,
            password="A-long-test-password-821!",
        )
        self.tech = TechnicianProfile.objects.create(
            user=self.tech_user, city_pool=self.pool
        )

    def test_public_database_is_not_automatically_seeded(self):
        self.assertEqual(CityPool.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_application_requires_post(self):
        self.client.force_login(self.tech_user)
        url = reverse("apply_job", args=[self.job.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("jobs"))
        self.assertTrue(
            Application.objects.filter(technician=self.tech, job=self.job).exists()
        )

    def test_city_pool_counts_are_database_backed(self):
        self.assertEqual(self.pool.technician_count, 1)
        self.assertEqual(self.pool.open_job_count, 1)

    def test_legacy_html_urls_redirect_to_clean_django_routes(self):
        redirects = {
            "/index.html": "/",
            "/home.html": "/",
            "/jobs.html": "/jobs/",
            "/city-pools.html": "/city-pools/",
            "/legal.html": "/legal/",
        }
        for legacy_url, clean_url in redirects.items():
            with self.subTest(legacy_url=legacy_url):
                response = self.client.get(legacy_url)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], clean_url)

    def test_technician_can_add_education_from_vault(self):
        self.client.force_login(self.tech_user)
        response = self.client.post(
            reverse("technician_vault"),
            {
                "action": "education",
                "school": "Columbus Technical Institute",
                "program": "Automotive Technology",
                "completion_year": "2024",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Education.objects.filter(
                technician=self.tech, program="Automotive Technology"
            ).exists()
        )

    def test_employer_cannot_edit_another_employers_job(self):
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            role=User.Role.EMPLOYER,
            password="A-long-test-password-821!",
        )
        EmployerProfile.objects.create(
            user=other_user,
            company_name="Other Auto",
            shop_type=EmployerProfile.ShopType.REPAIR,
        )
        self.client.force_login(other_user)
        self.assertEqual(
            self.client.get(reverse("employer_job_edit", args=[self.job.id])).status_code,
            404,
        )

    def test_invite_offer_and_accept_workflow(self):
        self.client.force_login(self.employer_user)
        response = self.client.post(
            reverse("invite_candidate", args=[self.tech.id]),
            {"job_id": self.job.id},
        )
        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(technician=self.tech, job=self.job)
        self.assertEqual(application.stage, Application.Stage.INVITED)

        self.client.force_login(self.tech_user)
        self.client.post(
            reverse("respond_application", args=[application.id]),
            {"response": "accept"},
        )
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.Stage.INTERVIEW)

        self.client.force_login(self.employer_user)
        self.client.post(
            reverse("update_application_stage", args=[application.id]),
            {"stage": Application.Stage.OFFERED, "offer_details": "Start Monday."},
        )
        self.client.force_login(self.tech_user)
        self.client.post(
            reverse("respond_application", args=[application.id]),
            {"response": "accept"},
        )
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.Stage.HIRED)

    def test_message_spam_guard_blocks_third_consecutive_message(self):
        application = Application.objects.create(technician=self.tech, job=self.job)
        self.client.force_login(self.employer_user)
        url = reverse("application_message", args=[application.id])
        self.client.post(url, {"body": "First"})
        self.client.post(url, {"body": "Second"})
        self.client.post(url, {"body": "Third"})
        self.assertEqual(ApplicationMessage.objects.filter(application=application).count(), 2)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
    )
    def test_notification_preferences_control_in_app_and_email_channels(self):
        preferences = NotificationPreference.objects.create(
            user=self.employer_user,
            in_app_applications=False,
            email_applications=False,
        )
        self.client.force_login(self.tech_user)
        self.client.post(reverse("apply_job", args=[self.job.id]))
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.employer_user,
                event=Notification.Event.APPLICATION,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 0)

        preferences.in_app_applications = True
        preferences.save(update_fields=["in_app_applications"])
        second_job = Job.objects.create(
            employer=self.employer,
            city_pool=self.pool,
            title="Second Diagnostic Technician",
            category=Job.Category.REPAIR,
            schedule=Job.Schedule.FULL_TIME,
            description="Second opening.",
            status=Job.Status.ACTIVE,
        )
        self.client.post(reverse("apply_job", args=[second_job.id]))
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.employer_user,
                event=Notification.Event.APPLICATION,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_saves_notification_checkboxes(self):
        self.client.force_login(self.tech_user)
        response = self.client.post(
            reverse("technician_vault"),
            {
                "action": "notifications",
                "in_app_messages": "on",
                "email_messages": "on",
                "in_app_offers": "on",
                "email_offers": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        preferences = NotificationPreference.objects.get(user=self.tech_user)
        self.assertTrue(preferences.in_app_messages)
        self.assertFalse(preferences.email_applications)
        self.assertFalse(preferences.email_credentials)


class PrivateDocumentTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.pool = CityPool.objects.create(
            name="Detroit",
            state="Michigan",
            state_code="MI",
            region=CityPool.Region.MIDWEST,
        )
        self.tech_user = User.objects.create_user(
            username="private-tech@example.com",
            email="private-tech@example.com",
            role=User.Role.TECHNICIAN,
            password="A-long-test-password-821!",
        )
        self.tech = TechnicianProfile.objects.create(
            user=self.tech_user, city_pool=self.pool
        )
        self.employer_user = User.objects.create_user(
            username="private-shop@example.com",
            email="private-shop@example.com",
            role=User.Role.EMPLOYER,
            password="A-long-test-password-821!",
        )
        self.employer = EmployerProfile.objects.create(
            user=self.employer_user,
            company_name="Private Shop",
            shop_type=EmployerProfile.ShopType.REPAIR,
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _upload(self, body=b"%PDF-1.4\nsafe test document"):
        self.client.force_login(self.tech_user)
        return self.client.post(
            reverse("technician_vault"),
            {
                "action": "document",
                "name": "Resume",
                "file": SimpleUploadedFile(
                    "resume.pdf", body, content_type="application/pdf"
                ),
            },
        )

    def test_valid_private_document_upload_and_owner_download(self):
        response = self._upload()
        self.assertEqual(response.status_code, 302)
        document = TechnicianDocument.objects.get(technician=self.tech)
        self.assertIn("private/technicians/", document.file.name)
        self.assertEqual(
            self.client.get(reverse("serve_document", args=[document.id])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/private-media/{document.file.name}").status_code, 404
        )

    def test_rejects_extension_content_mismatch(self):
        response = self._upload(body=b"MZ executable content")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TechnicianDocument.objects.exists())
        self.assertContains(response, "contents do not match")

    def test_rejects_oversized_file(self):
        response = self._upload(body=b"%PDF-" + b"x" * MAX_DOCUMENT_SIZE)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TechnicianDocument.objects.exists())
        self.assertContains(response, "10 MB or smaller")

    def test_employer_needs_approved_access(self):
        self._upload()
        document = TechnicianDocument.objects.get(technician=self.tech)
        self.client.force_login(self.employer_user)
        url = reverse("serve_document", args=[document.id])
        self.assertEqual(self.client.get(url).status_code, 403)
        access = CredentialAccessRequest.objects.create(
            employer=self.employer, technician=self.tech
        )
        self.assertEqual(self.client.get(url).status_code, 403)
        access.status = CredentialAccessRequest.Status.APPROVED
        access.save()
        document.is_verified = True
        document.save(update_fields=["is_verified"])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_approved_employer_cannot_download_unverified_upload(self):
        self._upload()
        document = TechnicianDocument.objects.get(technician=self.tech)
        CredentialAccessRequest.objects.create(
            employer=self.employer,
            technician=self.tech,
            status=CredentialAccessRequest.Status.APPROVED,
        )
        self.client.force_login(self.employer_user)
        response = self.client.get(reverse("serve_document", args=[document.id]))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "pending security review", status_code=403)

    def test_specific_credential_approval_does_not_expose_general_documents(self):
        self._upload()
        document = TechnicianDocument.objects.get(technician=self.tech)
        CredentialAccessRequest.objects.create(
            employer=self.employer,
            technician=self.tech,
            credential_type="ASE Master Technician",
            status=CredentialAccessRequest.Status.APPROVED,
        )
        self.client.force_login(self.employer_user)
        self.assertEqual(
            self.client.get(reverse("serve_document", args=[document.id])).status_code,
            403,
        )


class DemoDataTests(TestCase):
    @override_settings(DEBUG=True)
    def test_demo_seed_is_idempotent(self):
        call_command("seed_demo_data", verbosity=0)
        first = (
            CityPool.objects.count(),
            EmployerProfile.objects.count(),
            TechnicianProfile.objects.count(),
            Job.objects.count(),
            Application.objects.count(),
            Certification.objects.count(),
            Education.objects.count(),
            WorkHistory.objects.count(),
            ApplicationMessage.objects.count(),
            CredentialAccessRequest.objects.count(),
            Notification.objects.count(),
        )
        call_command("seed_demo_data", verbosity=0)
        second = (
            CityPool.objects.count(),
            EmployerProfile.objects.count(),
            TechnicianProfile.objects.count(),
            Job.objects.count(),
            Application.objects.count(),
            Certification.objects.count(),
            Education.objects.count(),
            WorkHistory.objects.count(),
            ApplicationMessage.objects.count(),
            CredentialAccessRequest.objects.count(),
            Notification.objects.count(),
        )
        self.assertEqual(first, (12, 7, 8, 12, 7, 4, 3, 3, 6, 3, 5))
        self.assertEqual(second, first)
