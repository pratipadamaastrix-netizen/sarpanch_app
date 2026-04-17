from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from .models import State, District, Constituency, Mandal, LocalBody


class StateResource(resources.ModelResource):
    class Meta:
        model = State


class DistrictResource(resources.ModelResource):
    class Meta:
        model = District


class ConstituencyResource(resources.ModelResource):
    class Meta:
        model = Constituency


class MandalResource(resources.ModelResource):
    class Meta:
        model = Mandal


class ConstituencyByNameAndDistrictWidget(ForeignKeyWidget):
    """
    Look up Constituency using visible constituency name (display_name)
    and district name. This matches how names appear in Excel/admin, e.g.
    \"Nalgonda (General)\".
    """

    def __init__(self):
        # Use display_name because that's what appears in Excel/admin
        super().__init__(Constituency, "display_name")

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        district_name = (row.get("district") or "").strip()
        qs = self.model.objects.filter(
            display_name=value.strip(),
            district__name=district_name,
        )
        try:
            return qs.get()
        except self.model.MultipleObjectsReturned:
            raise ValueError(
                f"Multiple constituencies named '{value}' in district '{district_name}'"
            )


class MandalByNameAndConstituencyWidget(ForeignKeyWidget):
    """
    Look up Mandal using both mandal name and constituency name,
    which matches the unique_together (constituency, name).
    """

    def __init__(self):
        super().__init__(Mandal, "name")

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        constituency_name = (row.get("constituency") or "").strip()
        district_name = (row.get("district") or "").strip()
        qs = self.model.objects.filter(
            name=value.strip(),
            constituency__display_name=constituency_name,
            constituency__district__name=district_name,
        )
        try:
            return qs.get()
        except self.model.MultipleObjectsReturned:
            raise ValueError(
                f"Multiple mandals named '{value}' in constituency '{constituency_name}' "
                f"and district '{district_name}'"
            )


class LocalBodyResource(resources.ModelResource):
    district = fields.Field(
        column_name="district",
        attribute="district",
        widget=ForeignKeyWidget(District, "name"),
    )
    constituency = fields.Field(
        column_name="constituency",
        attribute="constituency",
        widget=ConstituencyByNameAndDistrictWidget(),
    )
    mandal = fields.Field(
        column_name="mandal",
        attribute="mandal",
        widget=MandalByNameAndConstituencyWidget(),
    )
    is_active = fields.Field(
        column_name="is_active",
        attribute="is_active",
        widget=BooleanWidget(),
    )

    class Meta:
        model = LocalBody
        import_id_fields = ("name", "mandal", "local_body_type")
        fields = (
            "district",
            "constituency",
            "mandal",
            "name",
            "local_body_type",
            "pincode",
            "is_active",
        )

@admin.register(State)
class StateAdmin(ImportExportModelAdmin):
    resource_class = StateResource
    list_display = ("name", "code", "is_active", "created_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):
    resource_class = DistrictResource
    list_display = ("name", "state", "code", "is_active", "created_at")
    search_fields = ("name", "code", "state__name")
    list_filter = ("state", "is_active")
    ordering = ("name",)


@admin.register(Constituency)
class ConstituencyAdmin(ImportExportModelAdmin):
    resource_class = ConstituencyResource
    list_display = (
        "display_name",
        "district",
        "constituency_type",
        "is_active",
    )
    search_fields = (
        "name",
        "display_name",
        "district__name",
    )
    list_filter = ("district", "constituency_type", "is_active")
    ordering = ("display_name",)


@admin.register(Mandal)
class MandalAdmin(ImportExportModelAdmin):
    resource_class = MandalResource
    list_display = (
        "name",
        "district",
        "constituency",
        "display_order",
        "is_active",
    )
    search_fields = (
        "name",
        "district__name",
        "constituency__display_name",
    )
    list_filter = ("district", "constituency", "is_active")
    ordering = ("display_order", "name")


@admin.register(LocalBody)
class LocalBodyAdmin(ImportExportModelAdmin):
    resource_class = LocalBodyResource
    list_display = (
        "name",
        "local_body_type",
        "mandal",
        "constituency",
        "district",
        "is_active",
    )
    search_fields = (
        "name",
        "mandal__name",
        "constituency__display_name",
        "district__name",
    )
    list_filter = (
        "local_body_type",
        "district",
        "constituency",
        "mandal",
        "is_active",
    )
    ordering = ("name",)