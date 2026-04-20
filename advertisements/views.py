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

    base_ads = Advertisement.objects.filter(
        is_active=True,
        start_date__lte=today,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )

    ads = []

    # ✅ Priority with fallback
    if mandal_id:
        ads = base_ads.filter(mandal_id=mandal_id)

    if not ads and constituency_id:
        ads = base_ads.filter(constituency_id=constituency_id)

    if not ads and district_id:
        ads = base_ads.filter(district_id=district_id)

    if not ads:
        ads = base_ads  # fallback to all ads

    BASE_MEDIA_URL = "https://dev.maastrixdemo.com/testimg/"
        # "image": BASE_MEDIA_URL + ad.image.name,


    data = []
    for ad in ads:
        data.append({
            "title": ad.title,
            "image": BASE_MEDIA_URL +ad.image.name,
            #  "image": ad.image,
             "link": ad.link_url or "#",
        })
        
        
        
    
    return JsonResponse({"ads": data})