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
