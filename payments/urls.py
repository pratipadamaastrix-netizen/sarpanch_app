from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment_page, name="payment_page"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
]