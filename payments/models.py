from django.db import models
from django.contrib.auth.models import User


class Payment(models.Model):
    STATUS_CHOICES = (
        ("created", "Created"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")

    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=200, unique=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=500, blank=True, null=True)

    # Payment details
    amount = models.IntegerField()  # in paise (₹1 = 100)
    currency = models.CharField(max_length=10, default="INR")

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.amount}"