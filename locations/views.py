from django.http import JsonResponse
from .models import District, Constituency, Mandal, LocalBody


def get_districts(request, state_id):
    data = list(
        District.objects.filter(state_id=state_id)
        .order_by("name")
        .values("id", "name")
    )
    return JsonResponse({"results": data})


def get_constituencies(request, district_id):
    data = list(
        Constituency.objects.filter(district_id=district_id)
        .order_by("name")
        .values("id", "name")
    )
    return JsonResponse({"results": data})


def get_mandals(request, constituency_id):
    data = list(
        Mandal.objects.filter(constituency_id=constituency_id)
        .order_by("name")
        .values("id", "name")
    )
    return JsonResponse({"results": data})


def get_local_bodies(request, mandal_id):
    data = list(
        LocalBody.objects.filter(mandal_id=mandal_id)
        .order_by("name")
        .values("id", "name")
    )
    return JsonResponse({"results": data})

# Create your views here.
