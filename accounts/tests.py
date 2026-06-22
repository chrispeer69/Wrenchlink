from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import User
from marketplace.models import (
    Certification,
    EmployerProfile,
    TechnicianDocument,
    TechnicianProfile,
)


class AuthenticationTests(TestCase):
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
            )
        )
        self.technician_user.refresh_from_db()
        self.assertFalse(self.technician_user.is_active)

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

    def test_operations_mutations_require_post(self):
        self.client.force_login(self.staff)
        url = reverse(
            "accounts:operations_user_action",
            args=[self.technician_user.id, "suspend"],
        )
        self.assertEqual(self.client.get(url).status_code, 405)
