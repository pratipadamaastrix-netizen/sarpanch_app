from django.conf import settings


def email_dev_hint(_request):
    backend = getattr(settings, "EMAIL_BACKEND", "")
    return {
        "show_email_file_hint": settings.DEBUG
        and (
            "filebased" in backend
            or "OneEmailPerFile" in backend
        ),
    }
