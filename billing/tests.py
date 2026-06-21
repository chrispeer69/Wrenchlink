from django.test import TestCase
from django.urls import reverse


class BillingSecurityTests(TestCase):
    def test_unsigned_webhook_is_rejected(self):
        response = self.client.post(
            reverse("billing:webhook"),
            data=b"{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
