from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from advertisements.models import Advertisement, HomePageHero
from locations.models import District, Constituency, Mandal, LocalBody
from representatives.models import Representative


def _active_ads_queryset():
    today = timezone.now().date()
    return Advertisement.objects.filter(
        is_active=True,
        start_date__lte=today,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))


def _build_banner_slides():
    slides = []
    hero = (
        HomePageHero.objects.filter(is_active=True, show_first=True)
        .order_by("-updated_at")
        .first()
    )
    if hero and hero.image:
        slides.append(
            {
                "kind": "hero",
                "title": hero.title or "Welcome",
                "image": hero.image.url,
                "link": (hero.link_url or "").strip() or None,
            }
        )

    for ad in _active_ads_queryset().order_by("-created_at")[:5]:
        slides.append(
            {
                "kind": "ad",
                "title": ad.title,
                "image": ad.image.url,
                "link": (ad.link_url or "").strip() or None,
            }
        )
    return slides


def _stats():
    return {
        "districts": District.objects.filter(is_active=True).count(),
        "constituencies": Constituency.objects.filter(is_active=True).count(),
        "mandals": Mandal.objects.filter(is_active=True).count(),
        "villages": LocalBody.objects.filter(
            is_active=True, local_body_type="VILLAGE"
        ).count(),
        "representatives": Representative.objects.filter(status="ACTIVE").count(),
        "users": User.objects.filter(is_active=True).count(),
    }


def home(request):
    return render(
        request,
        "public/home.html",
        {
            "banner_slides": _build_banner_slides(),
            "stats": _stats(),
        },
    )


def about(request):
    return render(request, "public/about.html")


def contact(request):
    return render(request, "public/contact.html")
