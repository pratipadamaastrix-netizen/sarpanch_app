from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone

from .models import Advertisement
from django.db.models import Q


def get_ads(request):
    district_id = request.GET.get("district")
    constituency_id = request.GET.get("constituency")
    mandal_id = request.GET.get("mandal")

    today = timezone.now().date()

    ads = Advertisement.objects.filter(
    is_active=True,
    start_date__lte=today,
).filter(
    Q(end_date__isnull=True) | Q(end_date__gte=today)
)

    # 🔴 Priority logic (most specific first)

    if mandal_id:
        ads = ads.filter(mandal_id=mandal_id)

    elif constituency_id:
        ads = ads.filter(constituency_id=constituency_id)

    elif district_id:
        ads = ads.filter(district_id=district_id)

    # Prepare data for JSON
    data = []

    for ad in ads:
        data.append({
            "title": ad.title,
            "image": ad.image.url,
            "link": ad.link_url or "#",
        })

    return JsonResponse({"ads": data})