"""Helpers for accounts app."""

from datetime import date

from django.contrib.auth.models import User

from .models import UserProfile


def ensure_user_profile(user: User) -> UserProfile:
    """
    Return the user's UserProfile, creating a minimal row if missing
    (e.g. superuser or staff created in Django admin without registration).
    """
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "first_name": (user.first_name or "").strip() or "User",
            "last_name": (user.last_name or "").strip() or "—",
            "date_of_birth": date(1990, 1, 1),
        },
    )
    return profile
