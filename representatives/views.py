from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import SarpanchOtpForm, SarpanchPhoneForm, SarpanchUpdateForm
from .models import Representative
from .otp import (
    can_send_otp,
    find_representative_by_phone,
    generate_otp,
    increment_send_count,
    normalize_phone_digits,
    send_email_otp,
    send_sms_otp,
    store_otp,
    verify_and_consume_otp,
)

SESSION_REP_KEY = "representative_id"
SESSION_PENDING_PHONE_KEY = "sarpanch_pending_phone_digits"


def get_logged_in_representative(request):
    rid = request.session.get(SESSION_REP_KEY)
    if not rid:
        return None
    try:
        return Representative.objects.select_related(
            "local_body",
            "local_body__mandal",
            "local_body__constituency",
            "local_body__district",
        ).get(pk=rid, status="ACTIVE")
    except Representative.DoesNotExist:
        request.session.pop(SESSION_REP_KEY, None)
        return None


def sarpanch_login_phone_view(request):
    if get_logged_in_representative(request):
        return redirect("sarpanch_update_profile")

    if request.method == "POST":
        form = SarpanchPhoneForm(request.POST)
        if form.is_valid():
            digits = normalize_phone_digits(form.cleaned_data["mobile_number"])
            if len(digits) != 10:
                messages.error(request, "Enter a valid 10-digit mobile number.")
            else:
                rep = find_representative_by_phone(digits)
                if not rep:
                    messages.error(
                        request,
                        "No Sarpanch record found for this number. "
                        "Records are added by the administration.",
                    )
                elif not can_send_otp(digits):
                    messages.error(
                        request,
                        "Too many OTP requests. Please try again after some time.",
                    )
                else:
                    otp = generate_otp()
                    store_otp(digits, otp)
                    increment_send_count(digits)
                    send_sms_otp(digits, otp)
                    if rep.email and rep.email.strip():
                        send_email_otp(rep.email, otp)
                    request.session[SESSION_PENDING_PHONE_KEY] = digits
                    extra = " An OTP was also sent to your email." if rep.email else ""
                    messages.success(
                        request,
                        f"OTP sent to your mobile number.{extra}",
                    )
                    return redirect("sarpanch_login_verify")
    else:
        form = SarpanchPhoneForm()

    return render(
        request,
        "representatives/sarpanch_login_phone.html",
        {"form": form},
    )


def sarpanch_login_verify_view(request):
    if get_logged_in_representative(request):
        return redirect("sarpanch_update_profile")

    digits = request.session.get(SESSION_PENDING_PHONE_KEY)
    if not digits:
        messages.warning(request, "Enter your mobile number first.")
        return redirect("sarpanch_login")

    if request.method == "POST":
        form = SarpanchOtpForm(request.POST)
        if form.is_valid():
            if verify_and_consume_otp(digits, form.cleaned_data["otp"]):
                rep = find_representative_by_phone(digits)
                if rep:
                    request.session[SESSION_REP_KEY] = rep.pk
                    request.session.pop(SESSION_PENDING_PHONE_KEY, None)
                    messages.success(request, "Welcome. Please complete your profile.")
                    return redirect("sarpanch_update_profile")
            messages.error(request, "Invalid or expired OTP.")
    else:
        form = SarpanchOtpForm()

    return render(
        request,
        "representatives/sarpanch_login_otp.html",
        {
            "form": form,
            "masked_phone": f"******{digits[-4:]}",
        },
    )


def sarpanch_resend_otp_view(request):
    if request.method != "POST":
        return redirect("sarpanch_login_verify")

    digits = request.session.get(SESSION_PENDING_PHONE_KEY)
    if not digits:
        messages.warning(request, "Start again from Sarpanch login.")
        return redirect("sarpanch_login")

    rep = find_representative_by_phone(digits)
    if not rep:
        messages.error(request, "Session expired. Start again.")
        request.session.pop(SESSION_PENDING_PHONE_KEY, None)
        return redirect("sarpanch_login")

    if not can_send_otp(digits):
        messages.error(
            request,
            "Too many OTP requests. Please try again after some time.",
        )
        return redirect("sarpanch_login_verify")

    otp = generate_otp()
    store_otp(digits, otp)
    increment_send_count(digits)
    send_sms_otp(digits, otp)
    if rep.email and rep.email.strip():
        send_email_otp(rep.email, otp)
    messages.success(request, "A new OTP has been sent.")
    return redirect("sarpanch_login_verify")


def sarpanch_update_profile_view(request):
    rep = get_logged_in_representative(request)
    if not rep:
        messages.warning(request, "Please log in as Sarpanch first.")
        return redirect("sarpanch_login")

    if request.method == "POST":
        form = SarpanchUpdateForm(
            request.POST,
            request.FILES,
            instance=rep,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved successfully.")
            return redirect("sarpanch_update_profile")
    else:
        form = SarpanchUpdateForm(instance=rep)

    return render(
        request,
        "representatives/sarpanch_update_profile.html",
        {
            "form": form,
            "representative": rep,
        },
    )


def sarpanch_logout_view(request):
    request.session.pop(SESSION_REP_KEY, None)
    request.session.pop(SESSION_PENDING_PHONE_KEY, None)
    messages.success(request, "You have been logged out.")
    return redirect("login")
