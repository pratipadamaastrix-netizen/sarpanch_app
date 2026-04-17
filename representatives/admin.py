from django.contrib import admin
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import CharWidget, ForeignKeyWidget

from locations.models import LocalBody

from .models import Representative


class LocalBodyForRepresentativeWidget(ForeignKeyWidget):
    """
    Resolve Gram Panchayat (LocalBody, type VILLAGE) from the same columns
    as LocalBody bulk import: district, constituency (display_name), mandal, village (name).
    """

    def __init__(self):
        super().__init__(LocalBody, "name")

    def clean(self, value, row=None, *args, **kwargs):
        if not value or row is None:
            return None
        village_name = str(value).strip()
        district_name = (row.get("district") or "").strip()
        constituency_name = (row.get("constituency") or "").strip()
        mandal_name = (row.get("mandal") or "").strip()
        if not district_name or not mandal_name or not village_name:
            raise ValueError(
                "district, mandal, and village are required to find the Gram Panchayat."
            )
        qs = LocalBody.objects.filter(
            name=village_name,
            local_body_type="VILLAGE",
            district__name=district_name,
            mandal__name=mandal_name,
        )
        if constituency_name:
            qs = qs.filter(constituency__display_name=constituency_name)
        n = qs.count()
        if n == 1:
            return qs.first()
        if n == 0:
            extra = f", constituency={constituency_name}" if constituency_name else ""
            raise ValueError(
                f"No village '{village_name}' found for district={district_name}, "
                f"mandal={mandal_name}{extra}. Import LocalBody first or fix spelling."
            )
        raise ValueError(
            f"Multiple villages named '{village_name}' under this mandal. "
            "Add the constituency column (exact display_name as in admin) to pick one."
        )


class RepresentativeResource(resources.ModelResource):
    """
    Required Excel columns (same idea as LocalBody import):
    district, constituency, mandal, village (maps to local_body), full_name,
    mobile_number, plus optional fields below.

    Extra columns (district, constituency, mandal) are not model fields; they are
    read from each row when resolving ``village`` -> LocalBody.
    """

    local_body = fields.Field(
        column_name="village",
        attribute="local_body",
        widget=LocalBodyForRepresentativeWidget(),
    )
    representative_type = fields.Field(
        column_name="representative_type",
        attribute="representative_type",
        widget=CharWidget(),
    )
    status = fields.Field(
        column_name="status",
        attribute="status",
        widget=CharWidget(),
    )
    gender = fields.Field(
        column_name="gender",
        attribute="gender",
        widget=CharWidget(),
    )

    class Meta:
        model = Representative
        import_id_fields = ("local_body", "full_name", "mobile_number")
        fields = (
            "local_body",
            "representative_type",
            "full_name",
            "email",
            "age",
            "mobile_number",
            "gender",
            "status",
            "effective_from",
            "effective_to",
            "notes",
        )
        skip_unchanged = True

    def before_import(self, dataset, **kwargs):
        required = {
            "district",
            "constituency",
            "mandal",
            "village",
            "full_name",
            "mobile_number",
        }
        headers = set(dataset.headers or [])
        missing = required - headers
        if missing:
            raise ValueError(
                "Missing columns: "
                + ", ".join(sorted(missing))
                + ". Use the same location columns as LocalBody import "
                + "(district, constituency, mandal, village) plus full_name and mobile_number."
            )

    def before_import_row(self, row, **kwargs):
        rt = (row.get("representative_type") or "").strip().upper()
        if not rt:
            row["representative_type"] = "SARPANCH"
        st = (row.get("status") or "").strip().upper()
        if not st:
            row["status"] = "ACTIVE"
        for key in ("gender", "email", "notes"):
            v = row.get(key)
            if v is not None and str(v).strip() == "":
                row[key] = None
        age = row.get("age")
        if age is not None and str(age).strip() == "":
            row["age"] = None


@admin.register(Representative)
class RepresentativeAdmin(ImportExportModelAdmin):
    resource_class = RepresentativeResource

    list_display = (
        "photo_preview",
        "full_name",
        "email",
        "representative_type",
        "local_body",
        "mandal_name",
        "constituency_name",
        "district_name",
        "mobile_number",
        "age",
        "gender",
        "status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "mobile_number",
        "local_body__name",
        "local_body__mandal__name",
        "local_body__constituency__display_name",
        "local_body__district__name",
    )

    list_filter = (
        "representative_type",
        "status",
        "gender",
        "local_body__local_body_type",
        "local_body__district",
        "local_body__constituency",
        "local_body__mandal",
    )

    ordering = ("full_name",)

    readonly_fields = ("photo_preview_large", "created_at", "updated_at")

    fieldsets = (
        ("Representative Information", {
            "fields": (
                "local_body",
                "representative_type",
                "full_name",
                "email",
                "age",
                "gender",
                "mobile_number",
                "status",
            )
        }),
        ("Dates", {
            "fields": (
                "effective_from",
                "effective_to",
            )
        }),
        ("Photo", {
            "fields": (
                "photo",
                "photo_preview_large",
            )
        }),
        ("Additional Details", {
            "fields": (
                "notes",
            )
        }),
        ("System Info", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:6px;border:1px solid #ccc;" />',
                obj.photo.url
            )
        return "No Photo"
    photo_preview.short_description = "Photo"

    def photo_preview_large(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="160" style="border-radius:8px;border:1px solid #ccc;" />',
                obj.photo.url
            )
        return "No Photo Uploaded"
    photo_preview_large.short_description = "Photo Preview"

    def district_name(self, obj):
        return obj.local_body.district.name
    district_name.short_description = "District"
    district_name.admin_order_field = "local_body__district__name"

    def constituency_name(self, obj):
        return obj.local_body.constituency.display_name
    constituency_name.short_description = "Constituency"
    constituency_name.admin_order_field = "local_body__constituency__display_name"

    def mandal_name(self, obj):
        return obj.local_body.mandal.name
    mandal_name.short_description = "Mandal"
    mandal_name.admin_order_field = "local_body__mandal__name"
