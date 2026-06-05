import uuid
import secrets
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models


# Create your models here.


class Restaurant(models.Model):

    RESTAURANT_TYPES = [
        ("CASUAL", "Casual Dining"),
        ("FINE", "Fine Dining"),
        ("FAST", "Fast Food"),
        ("CAFE", "Cafe / Bakery"),
        ("BAR", "Bar / Pub"),
    ]

    name = models.CharField(max_length=150)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_restaurant",
    )
    restaurant_type = models.CharField(
        max_length=20, choices=RESTAURANT_TYPES, blank=True, null=True
    )
    is_onboarding_completed = models.BooleanField(default=False)

    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    logo = CloudinaryField("logo/", null=True, blank=True)
    primary_color = models.CharField(
        max_length=7, null=True, blank=True, help_text="hex color like #0EA5E9"
    )
    secondary_color = models.CharField(max_length=7, null=True, blank=True)
    theme = models.CharField(
        max_length=20, default="light", choices=[("light", "light"), ("dark", "dark")]
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Table(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manual_code = models.CharField(
        max_length=6,
        editable=False,
        blank=True,
        null=True,
    )
    
    restaurant = models.ForeignKey(
        "restaurants.Restaurant", on_delete=models.CASCADE, related_name="tables"
    )
    
    table_number = models.PositiveIntegerField()
    qr_code = models.ImageField(upload_to="table_qrCodes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.manual_code:
            while True:
                code = secrets.token_hex(3).upper()  # 6 chars
                if not Table.objects.filter(manual_code=code).exists():
                    self.manual_code = code
                    break

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("restaurant", "table_number")

    def __str__(self):
        return f"Table {self.table_number} - {self.restaurant.name}"
