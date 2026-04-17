from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment_page, name="payment_page"),
    path("success/", views.payment_success, name="payment_success"),
    path("failed/", views.payment_failed, name="payment_failed"),
]