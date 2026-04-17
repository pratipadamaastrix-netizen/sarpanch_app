from django.urls import path
from . import views

urlpatterns = [
    path("ajax/districts/<int:state_id>/", views.get_districts, name="get_districts"),
    path("ajax/constituencies/<int:district_id>/", views.get_constituencies, name="get_constituencies"),
    path("ajax/mandals/<int:constituency_id>/", views.get_mandals, name="get_mandals"),
    path("ajax/local-bodies/<int:mandal_id>/", views.get_local_bodies, name="get_local_bodies"),
]