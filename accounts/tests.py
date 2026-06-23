from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import ModerationAction, User
from marketplace.models import (
    Certification,
    EmployerProfile,
    Notification,
    TechnicianDocument,
    TechnicianProfile,
)


class AuthenticationTests(TestCase):
    def test_registration_location_dropdown_includes_other(self):
        technician_response = self.client.get(
            reverse("accounts:register_technician")
        )
        employer_response = self.client.get(reverse("accounts:register_employer"))
        self.assertContains(
            technician_response, "Other / location not listed"
        )
        self.assertContains(employer_response, "Other / location not listed")

    def test_superuser_creation_does_not_require_public_account_role(self):
        user = User.objects.create_superuser(
            username="admin",
            password="A-long-test-password-821!",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertIsNone(user.email)

    def test_technician_registration_creates_real_unverified_account(self):
        response = self.client.post(
            reverse("accounts:register_technician"),
            {
                "first_name": "Alex",
                "last_name": "Rivera",
                "email": "alex@example.com",
                "professional_title": "Master Technician",
                "city_pool": "",
                "password1": "A-long-test-password-821!",
                "password2": "A-long-test-password-821!",
            },
        )
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(email="alex@example.com")
        self.assertEqual(user.role, User.Role.TECHNICIAN)
        self.assertFalse(user.email_verified)
        self.assertTrue(hasattr(user, "technician_profile"))
        self.assertEqual(len(mail.outbox), 1)

    def test_unverified_user_cannot_sign_in(self):
        User.objects.create_user(
            username="tech@example.com",
            email="tech@example.com",
            role=User.Role.TECHNICIAN,
            password="A-long-test-password-821!",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "tech@example.com",
                "password": "A-long-test-password-821!",
            },
        )
        self.assertContains(response, "Verify your email")

    def test_verified_technician_login_routes_to_vault(self):
        user = User.objects.create_user(
            username="verified-tech@example.com",
            email="verified-tech@example.com",
            role=User.Role.TECHNICIAN,
            email_verified=True,
            password="A-long-test-password-821!",
        )
        TechnicianProfile.objects.create(user=user)
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "verified-tech@example.com",
                "password": "A-long-test-password-821!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("accounts:dashboard"))
        self.assertRedirects(
            self.client.get(reverse("accounts:dashboard")),
            reverse("technician_vault"),
        )

    def test_verified_employer_login_routes_to_dashboard(self):
        user = User.objects.create_user(
            username="verified-shop@example.com",
            email="verified-shop@example.com",
            role=User.Role.EMPLOYER,
            email_verified=True,
            password="A-long-test-password-821!",
        )
        EmployerProfile.objects.create(
            user=user,
            company_name="Verified Auto",
            shop_type=EmployerProfile.ShopType.REPAIR,
        )
        self.client.force_login(user)
        self.assertRedirects(
            self.client.get(reverse("accounts:dashboard")),
            reverse("employer_dashboard"),
        )


class OperationsPanelTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(
            username="operations-admin",
            password="A-long-test-password-821!",
        )
        self.technician_user = User.objects.create_user(
            username="operator-test@example.com",
            email="operator-test@example.com",
            role=User.Role.TECHNICIAN,
            email_verified=False,
            password="A-long-test-password-821!",
        )
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            professional_title="Diagnostic Technician",
        )
        self.document = TechnicianDocument.objects.create(
            technician=self.technician,
            name="Resume",
            file="private/technicians/test/resume.pdf",
        )
        self.certification = Certification.objects.create(
            technician=self.technician,
            name="ASE A6",
            file="private/technicians/test/ase.pdf",
        )

    def test_staff_dashboard_routes_to_branded_operations_panel(self):
        self.client.force_login(self.staff)
        self.assertRedirects(
            self.client.get(reverse("accounts:dashboard")),
            reverse("accounts:operations"),
        )
        response = self.client.get(reverse("accounts:operations"))
        self.assertContains(response, "Platform <em>operations</em>", html=True)
        self.assertContains(response, "Document review")

    def test_django_admin_links_to_branded_control_panel(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "WrenchLink Control Panel")
        self.assertContains(response, reverse("accounts:operations"))

    def test_non_staff_cannot_access_operations_panel(self):
        self.client.force_login(self.technician_user)
        self.assertEqual(
            self.client.get(reverse("accounts:operations")).status_code,
            403,
        )

    def test_staff_can_verify_and_suspend_public_user(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse(
                "accounts:operations_user_action",
                args=[self.technician_user.id, "verify-email"],
            )
        )
        self.assertEqual(response.status_code, 302)
        self.technician_user.refresh_from_db()
        self.assertTrue(self.technician_user.email_verified)

        self.client.post(
            reverse(
                "accounts:operations_user_action",
                args=[self.technician_user.id, "suspend"],
            ),
            {"reason": "Repeated violations of the marketplace rules."},
        )
        self.technician_user.refresh_from_db()
        self.assertFalse(self.technician_user.is_active)
        self.assertTrue(
            ModerationAction.objects.filter(
                target_user=self.technician_user,
                action="account_suspended",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.technician_user,
                event=Notification.Event.SYSTEM,
                body__icontains="marketplace rules",
            ).exists()
        )

    def test_staff_account_cannot_be_suspended_in_operations_panel(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse(
                "accounts:operations_user_action",
                args=[self.staff.id, "suspend"],
            )
        )
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_document_review_records_approval_and_rejection(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse(
                "accounts:operations_document_action",
                args=["document", self.document.id, "approve"],
            )
        )
        self.document.refresh_from_db()
        self.assertEqual(
            self.document.status, TechnicianDocument.Status.VERIFIED
        )
        self.assertTrue(self.document.is_verified)

        self.client.post(
            reverse(
                "accounts:operations_document_action",
                args=["certification", self.certification.id, "reject"],
            ),
            {"reason": "The credential number is unreadable."},
        )
        self.certification.refresh_from_db()
        self.assertEqual(
            self.certification.status, Certification.Status.REJECTED
        )
        self.assertFalse(self.certification.is_verified)
        self.assertEqual(
            self.certification.rejection_reason,
            "The credential number is unreadable.",
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.technician_user,
                body__icontains="credential number is unreadable",
            ).exists()
        )
        self.assertTrue(
            ModerationAction.objects.filter(
                target_user=self.technician_user,
                action="certification_reject",
            ).exists()
        )
        self.assertGreaterEqual(len(mail.outbox), 2)

    def test_rejection_requires_a_reason(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse(
                "accounts:operations_document_action",
                args=["document", self.document.id, "reject"],
            )
        )
        self.assertRedirects(
            response, f"{reverse('accounts:operations')}#documents"
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, TechnicianDocument.Status.PENDING)
        self.assertFalse(
            ModerationAction.objects.filter(
                target_user=self.technician_user,
                action="document_reject",
            ).exists()
        )

    def test_staff_can_send_direct_user_message(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse(
                "accounts:operations_send_message",
                args=[self.technician_user.id],
            ),
            {
                "subject": "Profile information required",
                "message": "Please add your current certification expiration dates.",
            },
        )
        self.assertRedirects(response, f"{reverse('accounts:operations')}#users")
        self.assertTrue(
            ModerationAction.objects.filter(
                target_user=self.technician_user,
                action="staff_message",
                subject="Profile information required",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.technician_user,
                title="Profile information required",
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("certification expiration dates", mail.outbox[0].body)

    def test_staff_can_reject_employer_with_persistent_reason(self):
        employer_user = User.objects.create_user(
            username="review-shop@example.com",
            email="review-shop@example.com",
            role=User.Role.EMPLOYER,
            email_verified=True,
            password="A-long-test-password-821!",
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            company_name="Review Auto",
            shop_type=EmployerProfile.ShopType.REPAIR,
        )
        self.client.force_login(self.staff)
        self.client.post(
            reverse(
                "accounts:operations_profile_action",
                args=["employer", employer.id, "reject"],
            ),
            {"reason": "Business ownership documents could not be verified."},
        )
        employer.refresh_from_db()
        self.assertEqual(
            employer.verification_status,
            EmployerProfile.VerificationStatus.REJECTED,
        )
        self.assertFalse(employer.is_verified)
        self.assertIn("ownership documents", employer.rejection_reason)
        self.assertTrue(
            Notification.objects.filter(
                recipient=employer_user,
                body__icontains="ownership documents",
            ).exists()
        )

    def test_operations_mutations_require_post(self):
        self.client.force_login(self.staff)
        url = reverse(
            "accounts:operations_user_action",
            args=[self.technician_user.id, "suspend"],
        )
        self.assertEqual(self.client.get(url).status_code, 405)
