from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("public.urls")),

    # User system
    path("accounts/", include("accounts.urls")),

    # Location hierarchy
    path("locations/", include("locations.urls")),

    # ⭐ ADD THIS LINE — Payment system
    path("payments/", include("payments.urls")),

    # ⭐ ADD THIS
    path("advertisements/", include("advertisements.urls")),
]

# ✅ REMOVE DEBUG CONDITION
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)