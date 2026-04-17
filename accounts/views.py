import logging

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

from .models import UserProfile
from .utils import ensure_user_profile
from .forms import (
    RegisterForm,
    LoginForm,
    EditProfileForm,
    ForgotPasswordUsernameForm,
    ForgotPasswordEmailForm,
    ForgotPasswordOTPForm,
    AppSetPasswordForm,
)
from .password_reset_otp import (
    can_send_password_reset_otp,
    generate_otp,
    increment_password_reset_send_count,
    send_password_reset_email,
    send_password_reset_sms,
    store_password_reset_otp,
    verify_and_consume_password_reset_otp,
)

from locations.models import District, Constituency, Mandal, LocalBody
from representatives.models import Representative

# in any views.py
from django.http import HttpResponse
import os
from django.conf import settings

def check_static(request):
    path = os.path.join(settings.BASE_DIR, 'staticfiles')
    files = os.listdir(path) if os.path.exists(path) else "NOT FOUND"
    return HttpResponse(str(files))

PWD_RESET_USERNAME = "pwd_reset_username"
PWD_RESET_UID = "pwd_reset_uid"
PWD_RESET_OTP_OK = "pwd_reset_otp_ok"


def _clear_password_reset_session(request):
    request.session.pop(PWD_RESET_USERNAME, None)
    request.session.pop(PWD_RESET_UID, None)
    request.session.pop(PWD_RESET_OTP_OK, None)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    request.session.pop("representative_id", None)

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"].strip(),
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )

            UserProfile.objects.create(
                user=user,
                first_name=form.cleaned_data["first_name"],
                middle_name=form.cleaned_data.get("middle_name", ""),
                last_name=form.cleaned_data["last_name"],
                date_of_birth=form.cleaned_data["date_of_birth"],
                state=form.cleaned_data["state"],
                district=form.cleaned_data["district"],
                constituency=form.cleaned_data["constituency"],
                mandal=form.cleaned_data["mandal"],
                local_body=form.cleaned_data["local_body"],
                phone_number=form.cleaned_data["phone_number"],
                is_paid_user=False,
            )

            messages.success(request, "Registration completed successfully. Please login.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session.pop("representative_id", None)

            profile = ensure_user_profile(user)

            if profile.is_paid_user:
                return redirect("dashboard")
            else:
                return redirect("payment_page")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


@login_required
def dashboard_view(request):

    # 🟢 PAYMENT GATE CHECK
    profile = ensure_user_profile(request.user)
    # ⭐ ADD THIS
    default_district = profile.district.id if profile.district else None

    if not profile.is_paid_user:
        return redirect("payment_page")

    # ----------------------------
    # EXISTING DASHBOARD LOGIC
    # (keep your current code below)
    # ----------------------------

    districts = District.objects.filter(is_active=True).order_by("name")

    selected_district = request.GET.get("district", "")
    selected_constituency = request.GET.get("constituency", "")
    selected_mandal = request.GET.get("mandal", "")
    selected_local_body = request.GET.get("local_body", "")

    constituencies = Constituency.objects.none()
    mandals = Mandal.objects.none()
    local_bodies = LocalBody.objects.none()
    representative = None

    if selected_district:
        constituencies = Constituency.objects.filter(
            district_id=selected_district,
            is_active=True
        ).order_by("name")

    if selected_constituency:
        mandals = Mandal.objects.filter(
            constituency_id=selected_constituency,
            is_active=True
        ).order_by("display_order", "name")

    if selected_mandal:
        local_bodies = LocalBody.objects.filter(
            mandal_id=selected_mandal,
            is_active=True
        ).order_by("name")

    if selected_local_body:
        representative = Representative.objects.filter(
            local_body_id=selected_local_body
        ).select_related(
            "local_body",
            "local_body__mandal",
            "local_body__constituency",
            "local_body__district",
        ).first()

    context = {
        "districts": districts,
        "constituencies": constituencies,
        "mandals": mandals,
        "local_bodies": local_bodies,
        "representative": representative,
        "selected_district": str(selected_district),
        "selected_constituency": str(selected_constituency),
        "selected_mandal": str(selected_mandal),
        "selected_local_body": str(selected_local_body),
        "default_district": default_district,
    }

    return render(request, "accounts/dashboard.html", context)


@login_required
def profile_view(request):
    profile = ensure_user_profile(request.user)

    context = {
        "profile": profile,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile_view(request):
    profile = ensure_user_profile(request.user)
    user = request.user

    if request.method == "POST":
        form = EditProfileForm(request.POST, user=user)
        if form.is_valid():
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            profile.first_name = form.cleaned_data["first_name"]
            profile.middle_name = form.cleaned_data.get("middle_name", "")
            profile.last_name = form.cleaned_data["last_name"]
            profile.date_of_birth = form.cleaned_data["date_of_birth"]
            profile.state = form.cleaned_data["state"]
            profile.district = form.cleaned_data["district"]
            profile.constituency = form.cleaned_data["constituency"]
            profile.mandal = form.cleaned_data["mandal"]
            profile.local_body = form.cleaned_data["local_body"]
            profile.phone_number = form.cleaned_data["phone_number"]
            profile.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(
            user=user,
            initial={
            "email": user.email,
            "phone_number": profile.phone_number or "",
            "first_name": profile.first_name,
            "middle_name": profile.middle_name,
            "last_name": profile.last_name,
            "date_of_birth": profile.date_of_birth,
            "state": profile.state.id if profile.state else None,
            "district": profile.district.id if profile.district else None,
            "constituency": profile.constituency.id if profile.constituency else None,
            "mandal": profile.mandal.id if profile.mandal else None,
            "local_body": profile.local_body.id if profile.local_body else None,
        },
        )

    return render(request, "accounts/edit_profile.html", {"form": form})


def password_reset_username_view(request):
    """Step 1: enter username."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "GET":
        _clear_password_reset_session(request)

    if request.method == "POST":
        form = ForgotPasswordUsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"].strip()
            user = User.objects.filter(username__iexact=username, is_active=True).first()
            if not user:
                messages.error(request, "No active account found with that username.")
            else:
                request.session[PWD_RESET_USERNAME] = user.username
                return redirect("password_reset_email")
    else:
        form = ForgotPasswordUsernameForm()

    return render(request, "accounts/password_reset_username.html", {"form": form})


def password_reset_email_view(request):
    """Step 2: confirm email; sends the same OTP to SMS and email."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    username = request.session.get(PWD_RESET_USERNAME)
    if not username:
        messages.warning(request, "Start by entering your username.")
        return redirect("password_reset")

    try:
        user = User.objects.get(username__iexact=username, is_active=True)
    except User.DoesNotExist:
        _clear_password_reset_session(request)
        messages.error(request, "Session expired. Please start again.")
        return redirect("password_reset")

    profile = ensure_user_profile(user)

    if not profile.phone_number:
        messages.error(
            request,
            "No mobile number on file. Add your phone in Edit profile (after login) or ask an administrator.",
        )
        return redirect("password_reset")

    if not (user.email or "").strip():
        messages.error(
            request,
            "No email on file for this account. Ask an administrator to set your email.",
        )
        return redirect("password_reset")

    if request.method == "POST":
        form = ForgotPasswordEmailForm(request.POST)
        if form.is_valid():
            entered = (form.cleaned_data["email"] or "").strip()
            if entered.lower() != (user.email or "").strip().lower():
                messages.error(request, "That email does not match our records for this username.")
            elif not can_send_password_reset_otp(user.id):
                messages.error(
                    request,
                    "Too many OTP requests. Please try again after some time.",
                )
            else:
                otp = generate_otp()
                store_password_reset_otp(user.id, otp)
                send_password_reset_sms(profile.phone_number, otp)
                send_password_reset_email(user.email, otp)
                increment_password_reset_send_count(user.id)
                request.session[PWD_RESET_UID] = user.id
                request.session[PWD_RESET_OTP_OK] = False
                logger.info("Password reset OTP issued for user id=%s", user.id)
                messages.success(
                    request,
                    "We sent a 6-digit OTP to your mobile (+91) and to your email. Enter it on the next step.",
                )
                return redirect("password_reset_verify")
    else:
        form = ForgotPasswordEmailForm()

    return render(
        request,
        "accounts/password_reset_email.html",
        {"form": form, "username": user.username},
    )


def password_reset_verify_view(request):
    """Step 3: enter OTP (same code works from SMS or email)."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    uid = request.session.get(PWD_RESET_UID)
    if not uid:
        messages.warning(request, "Start the reset flow from the beginning.")
        return redirect("password_reset")

    user = User.objects.filter(pk=uid, is_active=True).first()
    if not user:
        _clear_password_reset_session(request)
        return redirect("password_reset")

    if request.method == "POST" and request.POST.get("resend"):
        if not can_send_password_reset_otp(user.id):
            messages.error(
                request,
                "Too many OTP requests. Please try again after some time.",
            )
        else:
            profile = ensure_user_profile(user)
            if not profile.phone_number or not (user.email or "").strip():
                messages.error(request, "Cannot resend OTP. Start again.")
                return redirect("password_reset")
            otp = generate_otp()
            store_password_reset_otp(user.id, otp)
            send_password_reset_sms(profile.phone_number, otp)
            send_password_reset_email(user.email, otp)
            increment_password_reset_send_count(user.id)
            messages.success(request, "A new OTP has been sent to your mobile and email.")
        return redirect("password_reset_verify")

    if request.method == "POST":
        form = ForgotPasswordOTPForm(request.POST)
        if form.is_valid():
            ok = verify_and_consume_password_reset_otp(user.id, form.cleaned_data["otp"])
            if not ok:
                messages.error(request, "Invalid or expired OTP.")
            else:
                request.session[PWD_RESET_OTP_OK] = True
                return redirect("password_reset_set_password")
    else:
        form = ForgotPasswordOTPForm()

    return render(request, "accounts/password_reset_otp.html", {"form": form})


def password_reset_set_password_view(request):
    """Step 4: new password after OTP verified."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    uid = request.session.get(PWD_RESET_UID)
    if not uid or not request.session.get(PWD_RESET_OTP_OK):
        messages.warning(request, "Verify the OTP first.")
        return redirect("password_reset")

    user = User.objects.filter(pk=uid, is_active=True).first()
    if not user:
        _clear_password_reset_session(request)
        return redirect("password_reset")

    if request.method == "POST":
        form = AppSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            _clear_password_reset_session(request)
            messages.success(request, "Your password has been updated. You can log in now.")
            return redirect("login")
    else:
        form = AppSetPasswordForm(user)

    return render(request, "accounts/password_reset_set_password.html", {"form": form})