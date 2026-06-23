from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class WrenchLinkUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        user = self.model(
            username=self.model.normalize_username(username),
            email=self.normalize_email(email) if email else None,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    class Role(models.TextChoices):
        TECHNICIAN = "technician", "Technician"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TECHNICIAN,
    )
    email_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = []
    objects = WrenchLinkUserManager()

    def __str__(self):
        return self.get_full_name() or self.email


class ModerationAction(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions_taken",
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="moderation_actions_received",
    )
    action = models.CharField(max_length=60)
    subject = models.CharField(max_length=180)
    message = models.CharField(max_length=600, blank=True)
    object_type = models.CharField(max_length=40, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action}: {self.target_user}"
