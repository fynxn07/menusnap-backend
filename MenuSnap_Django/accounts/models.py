import uuid

from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager

# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Admin"
        RESTAURANT_ADMIN = "RESTAURANT_ADMIN", "Restaurant Admin"
        KITCHEN_STAFF = "KITCHEN_STAFF", "Kitchen Staff"
        WAITER = "WAITER", "Waiter"

    restaurant = models.ForeignKey(
        "restaurants.Restaurant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.RESTAURANT_ADMIN
    )

    profile_image = CloudinaryField("profile", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email


class InactiveEmailLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "sent_at"])]


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    session_token = models.UUIDField(default=uuid.uuid4, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "otp"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} (verified={self.is_verified})"
