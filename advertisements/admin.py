from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Advertisement, HomePageHero


@admin.register(HomePageHero)
class HomePageHeroAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "title",
        "is_active",
        "show_first",
        "updated_at",
    )
    list_filter = ("is_active", "show_first")
    search_fields = ("title",)
    readonly_fields = ("image_preview_large", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "image", "image_preview_large", "link_url", "is_active", "show_first")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="40" style="object-fit:cover;border-radius:6px;border:1px solid #ccc;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Preview"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="320" style="border-radius:8px;border:1px solid #ccc;max-width:100%;" />',
                obj.image.url,
            )
        return "No image"
    image_preview_large.short_description = "Preview"


class AdvertisementResource(resources.ModelResource):
    class Meta:
        model = Advertisement
        import_id_fields = ("title", "district", "constituency", "mandal", "start_date")
        fields = (
            "id",
            "title",
            "image",
            "link_url",
            "district",
            "constituency",
            "mandal",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        )


@admin.register(Advertisement)
class AdvertisementAdmin(ImportExportModelAdmin):
    resource_class = AdvertisementResource

    list_display = (
        "image_preview",
        "title",
        "district",
        "constituency",
        "mandal",
        "is_active",
        "start_date",
        "end_date",
        "created_at",
    )

    list_filter = (
        "district",
        "constituency",
        "mandal",
        "is_active",
        "start_date",
        "end_date",
    )

    search_fields = (
        "title",
        "district__name",
        "constituency__display_name",
        "mandal__name",
    )

    ordering = ("-created_at",)

    readonly_fields = ("image_preview_large", "created_at")

    fieldsets = (
        ("Advertisement Details", {
            "fields": (
                "title",
                "link_url",
                "is_active",
            )
        }),
        ("Location Targeting", {
            "fields": (
                "district",
                "constituency",
                "mandal",
            )
        }),
        ("Dates", {
            "fields": (
                "start_date",
                "end_date",
            )
        }),
        ("Image", {
            "fields": (
                "image",
                "image_preview_large",
            )
        }),
        ("System Info", {
            "fields": (
                "created_at",
            )
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="70" height="40" style="object-fit:cover;border-radius:6px;border:1px solid #ccc;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="220" style="border-radius:8px;border:1px solid #ccc;" />',
                obj.image.url
            )
        return "No Image Uploaded"
    image_preview_large.short_description = "Image Preview"