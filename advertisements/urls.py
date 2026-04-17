from django.urls import path
from . import views

urlpatterns = [
    path("ajax/get-ads/", views.get_ads, name="get_ads"),
]