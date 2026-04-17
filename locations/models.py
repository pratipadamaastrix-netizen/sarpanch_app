from django.db import models


class BaseTimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class State(BaseTimestampModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(BaseTimestampModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("state", "name")

    def __str__(self):
        return self.name


class Constituency(BaseTimestampModel):
    CONSTITUENCY_TYPE_CHOICES = [
        ("GENERAL", "General"),
        ("SC", "SC"),
        ("ST", "ST"),
    ]

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="constituencies",
    )
    name = models.CharField(max_length=150)
    display_name = models.CharField(max_length=200)
    constituency_type = models.CharField(
        max_length=20,
        choices=CONSTITUENCY_TYPE_CHOICES,
        default="GENERAL",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("district", "name")

    def __str__(self):
        return self.display_name


class Mandal(BaseTimestampModel):
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="mandals",
    )
    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.CASCADE,
        related_name="mandals",
    )
    name = models.CharField(max_length=150)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = ("constituency", "name")

    def __str__(self):
        return self.name


class LocalBody(BaseTimestampModel):
    LOCAL_BODY_TYPE_CHOICES = [
        ("VILLAGE", "Village"),
        ("MUNICIPALITY", "Municipality"),
    ]

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="local_bodies",
    )
    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.CASCADE,
        related_name="local_bodies",
    )
    mandal = models.ForeignKey(
        Mandal,
        on_delete=models.CASCADE,
        related_name="local_bodies",
    )
    name = models.CharField(max_length=200)
    local_body_type = models.CharField(
        max_length=20,
        choices=LOCAL_BODY_TYPE_CHOICES,
    )
    pincode = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("mandal", "name", "local_body_type")

    def __str__(self):
        return f"{self.name} ({self.local_body_type})"

# Create your models here.
