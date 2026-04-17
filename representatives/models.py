from django.db import models
from locations.models import LocalBody


class BaseTimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Representative(BaseTimestampModel):
    REPRESENTATIVE_TYPE_CHOICES = [
        ("SARPANCH", "Sarpanch"),
        ("CHAIRPERSON", "Chairperson"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    local_body = models.ForeignKey(
        LocalBody,
        on_delete=models.CASCADE,
        related_name="representatives"
    )
    representative_type = models.CharField(
        max_length=20,
        choices=REPRESENTATIVE_TYPE_CHOICES
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        help_text="Optional. Used for OTP when Sarpanch logs in.",
    )
    age = models.PositiveIntegerField(blank=True, null=True)
    mobile_number = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="representatives/", blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    effective_from = models.DateField(blank=True, null=True)
    effective_to = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.representative_type}"

# Create your models here.
