from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import User
from marketplace.models import EmployerProfile, TechnicianProfile


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
