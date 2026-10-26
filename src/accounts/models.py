from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models


class EmailUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        name = extra_fields.get("name")
        if name is not None:
            extra_fields["name"] = name.strip()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = EmailUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("email"),
                name="accounts_user_email_ci_unique",
            )
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email or "")
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError({"name": "نام الزامی است."})

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email or "")
        self.name = (self.name or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.email})"
