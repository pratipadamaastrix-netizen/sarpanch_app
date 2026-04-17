from django.db import models
from django.contrib.auth.models import User
from locations.models import State, District, Constituency, Mandal, LocalBody


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField()

    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    constituency = models.ForeignKey(Constituency, on_delete=models.SET_NULL, null=True)
    mandal = models.ForeignKey(Mandal, on_delete=models.SET_NULL, null=True)
    local_body = models.ForeignKey(LocalBody, on_delete=models.SET_NULL, null=True)

    phone_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        help_text="10-digit Indian mobile number (without +91).",
    )

    is_paid_user = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# Create your models here.
